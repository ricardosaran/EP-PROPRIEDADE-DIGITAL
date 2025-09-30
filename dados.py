# -*- coding: utf-8 -*-
from pathlib import Path
import re
import pandas as pd
import numpy as np

# ====== RAIZ ONDE ESTÃO AS PASTAS/ARQUIVOS DE RESULTADOS ======
ROOT_DIR = Path(r"C:\Users\ricardosa\Documents\docs relatórios ep\compilação")
OUT_PATH = ROOT_DIR / "master_resultados.xlsx"
# ===============================================================

def achar_arquivos(root: Path) -> list[Path]:
    # pega qualquer arquivo que contenha 'resultados' ou 'resultado' no nome
    pats = ["**/*resultados*.xlsx", "**/*resultado*.xlsx"]
    vistos, arquivos = set(), []
    for pat in pats:
        for p in root.glob(pat):
            if p.is_file() and p.suffix.lower() == ".xlsx":
                rp = p.resolve()
                if rp not in vistos:
                    vistos.add(rp)
                    arquivos.append(p)
    return sorted(arquivos, key=lambda x: x.as_posix().lower())

def inferir_grupo(path: Path) -> str:
    m = re.search(r"(.*)_resultados\.xlsx$", path.name, flags=re.IGNORECASE)
    if m: return m.group(1)
    m = re.search(r"resultado\s+(.+)\.xlsx$", path.name, flags=re.IGNORECASE)
    if m: return m.group(1)
    return path.parent.name

def ler_abas(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    comp = niv = fin = pd.DataFrame()
    try: comp = pd.read_excel(path, sheet_name="comparativo", engine="openpyxl")
    except Exception: pass
    try: niv  = pd.read_excel(path, sheet_name="resumo_niveis", engine="openpyxl")
    except Exception: pass
    try: fin  = pd.read_excel(path, sheet_name="financeiro_resumo", engine="openpyxl")
    except Exception: pass
    return comp, niv, fin

def main():
    arquivos = achar_arquivos(ROOT_DIR)
    if not arquivos:
        print(f"⚠️ Nenhum '*resultado*.xlsx' encontrado em {ROOT_DIR}")
        return

    comps, nives, fins = [], [], []

    print("🔎 Encontrados:")
    for p in arquivos:
        print(" •", p)

    for p in arquivos:
        grupo = inferir_grupo(p).strip()
        comp, niv, fin = ler_abas(p)

        if not comp.empty:
            comp = comp.copy(); comp.insert(0, "Grupo", grupo); comps.append(comp)
        else:
            print(f"↪️ {p.name}: aba 'comparativo' ausente (pulando)")

        if not niv.empty:
            niv = niv.copy(); niv.insert(0, "Grupo", grupo)
            if "Nível" not in niv.columns:
                poss = [c for c in niv.columns if "nível" in str(c).lower() or "nivel" in str(c).lower()]
                if poss: niv = niv.rename(columns={poss[0]: "Nível"})
            if "Qtd Inicial" not in niv.columns:
                poss = [c for c in niv.columns if "inicial" in str(c).lower()]
                if poss: niv = niv.rename(columns={poss[0]: "Qtd Inicial"})
            if "Qtd Final" not in niv.columns:
                poss = [c for c in niv.columns if "final" in str(c).lower()]
                if poss: niv = niv.rename(columns={poss[0]: "Qtd Final"})
            nives.append(niv)
        else:
            print(f"↪️ {p.name}: aba 'resumo_niveis' ausente (pulando)")

        if not fin.empty:
            fin = fin.copy(); fin.insert(0, "Grupo", grupo); fins.append(fin)
        else:
            print(f"↪️ {p.name}: aba 'financeiro_resumo' ausente (pulando)")

    if not comps and not nives and not fins:
        print("❌ Nada para consolidar.")
        return

    # ===== comparativo_master
    comp_master = pd.concat(comps, ignore_index=True) if comps else pd.DataFrame()

    # ===== niveis_master + TOTAL
    if nives:
        niv_master = pd.concat(nives, ignore_index=True)
        for c in ["Nível", "Qtd Inicial", "Qtd Final"]:
            if c not in niv_master.columns: niv_master[c] = 0
        total_geral = (
            niv_master.groupby("Nível", as_index=False)[["Qtd Inicial","Qtd Final"]]
            .sum().assign(Grupo="TOTAL")
        )
        order = pd.CategoricalDtype(["Básico","Intermediário","Avançado"], ordered=True)
        niv_master["Nível"] = niv_master["Nível"].astype(order)
        niv_master = niv_master.sort_values(["Grupo","Nível"], na_position="last")
        niv_master_full = pd.concat([niv_master, total_geral], ignore_index=True)
    else:
        niv_master_full = pd.DataFrame(columns=["Grupo","Nível","Qtd Inicial","Qtd Final"])

    # ===== financeiro_master + TOTAL
    if fins:
        fin_master = pd.concat(fins, ignore_index=True)
        for c in ["Soma Inicial (todos)","Soma Final (todos)"]:
            if c not in fin_master.columns: fin_master[c] = 0.0
        soma_i = pd.to_numeric(fin_master["Soma Inicial (todos)"], errors="coerce").sum()
        soma_f = pd.to_numeric(fin_master["Soma Final (todos)"], errors="coerce").sum()
        total_row = {
            "Grupo": "TOTAL",
            "Bloco": "Gestão Financeira",
            "Soma Inicial (todos)": soma_i,
            "Soma Final (todos)": soma_f,
            "Evolução Absoluta": soma_f - soma_i,
            "% sobre Inicial": (soma_f - soma_i) / soma_i * 100.0 if soma_i else np.nan
        }
        fin_master_full = pd.concat([fin_master, pd.DataFrame([total_row])], ignore_index=True)
    else:
        fin_master_full = pd.DataFrame(columns=["Grupo","Bloco","Soma Inicial (todos)","Soma Final (todos)","Evolução Absoluta","% sobre Inicial"])

    with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as w:
        if not comp_master.empty:      comp_master.to_excel(w, sheet_name="comparativo_master", index=False)
        if not niv_master_full.empty:  niv_master_full.to_excel(w, sheet_name="niveis_master", index=False)
        if not fin_master_full.empty:  fin_master_full.to_excel(w, sheet_name="financeiro_master", index=False)

    print(f"✅ Consolidado salvo em: {OUT_PATH}")

if __name__ == "__main__":
    main()
