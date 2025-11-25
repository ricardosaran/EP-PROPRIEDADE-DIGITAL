# app_unificado.py
# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime

# Plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Pacote 'plotly' não está instalado. Rode: pip install plotly")
    st.stop()

# --------- CSS VISUAL ---------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .card {
        background:#f1f5fa;
        border-radius:13px;
        padding:16px 28px 8px 28px;
        box-shadow:0 2px 4px 0 rgba(120,120,140,0.13);
        border:2px solid #dee5ed;
        text-align: center; 
    }
    
    .kpi-label {color:#366093;font-size:16.5px;font-weight:400;}
    .kpi-value {color:#084074;font-size:29px;font-weight:700;margin-top:4px;}
    .kpi-value-cancel {color:#e85b41;}
    .kpi-value-pend {color:#e0972c;}
    .section-box {background:#f3f5fa;border-radius:14px;border:1.5px solid #d4dae6;padding:24px 14px 18px 22px;margin-bottom:26px;}
    .js-plotly-plot, .js-plotly-plot .plot-container, .js-plotly-plot .main-svg {
        overflow: visible !important;
    }

    /* Adiciona espaço entre os nomes das abas */
    button[data-baseweb="tab"] {
        margin: 0 10px; /* Adiciona 10px de margem em cada lado */
    }

    </style>
""", unsafe_allow_html=True)

# ================== CORES (AZUL CLARO/ESCURO) ==================
cores_principais = ['#084074', '#6AA4D9', '#F2E77F', '#252525']
mapa_cores_sim_nao = {'Sim': '#084074', 'Não': '#6AA4D9'}

mapa_cores_evolucao = {
    'Pontuação Inicial': '#6AA4D9', # Azul Mais Claro
    'Pontuação Final': '#084074',   # Azul Escuro
    'Qtd Inicial': '#6AA4D9',       
    'Qtd Final': '#084074',         
    'Soma Inicial': '#6AA4D9',      
    'Soma Final': '#084074'         
}

NIVEIS_ORDER = ["Básico", "Intermediário", "Avançado"]
cor_grafico_principal = '#084074'

# ==============================================================================
# -------------------- ⚠️ DATA DE ATUALIZAÇÃO MANUAL ⚠️ --------------------
# ==============================================================================
# ALTERE AQUI A DATA E HORA PARA ATUALIZAR O PAINEL:
DATA_MANUAL = "17/11/2025 19:15:00" 
# ==============================================================================


# --------- FUNÇÕES DE ESTILO PLOTLY ---------
def add_plotly_border(fig: go.Figure, color="#333", width=2, pad=0.004):
    x0, y0 = 0 + pad, 0 + pad
    x1, y1 = 1 - pad, 1 - pad
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line=dict(color=color, width=width),
        layer="above"
    )
    return fig

def style_fig(fig: go.Figure, border_color="#333", border_width=2, pad=0.004) -> go.Figure:
    fig.update_layout(
        margin=dict(l=48, r=48, t=64, b=48),
        paper_bgcolor="white",
        plot_bgcolor="white",
        bargap=0.15,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    add_plotly_border(fig, border_color, border_width, pad)
    return fig

# --------- CARREGAMENTO DE DADOS (CACHE BASEADO NA DATA MANUAL) ---------
@st.cache_data
def load_all_data(data_versao): 
    # O parâmetro 'data_versao' serve para forçar a recarga quando a DATA_MANUAL muda
    excel_file_path = "master_resultados.xlsx"
    
    comparativo_df = pd.read_excel(excel_file_path, sheet_name="comparativo_master")
    niveis_df = pd.read_excel(excel_file_path, sheet_name="niveis_master")
    financeiro_df = pd.read_excel(excel_file_path, sheet_name="financeiro_master")
    questionario_df = pd.read_excel(excel_file_path, sheet_name="questionario")
    status_df = pd.read_excel(excel_file_path, sheet_name="status_consultorias")

    try:
        canceladas_df = pd.read_excel(excel_file_path, sheet_name="canceladas_detalhe")
    except Exception as e:
        st.sidebar.error("Aba 'canceladas_detalhe' não encontrada no Excel.")
        canceladas_df = pd.DataFrame(columns=["COOPERATIVA"])

    for df in [comparativo_df, niveis_df, financeiro_df, questionario_df, status_df, canceladas_df]:
        df.columns = df.columns.str.strip()

    for col in questionario_df.select_dtypes(include=['object']).columns:
      questionario_df[col] = questionario_df[col].astype(str).str.strip()

    questionario_df.rename(columns={'COOPERATIVA': 'Grupo', 'CLIENTE': 'Cliente'}, inplace=True)
    merged_df = pd.merge(comparativo_df, questionario_df, on=['Grupo', 'Cliente'], how='left')

    return merged_df, niveis_df, financeiro_df, status_df, canceladas_df

# ================== CARREGAMENTO PRINCIPAL ==================
comparativo_df, niveis_df, financeiro_df, status_df, canceladas_df = load_all_data(data_versao=DATA_MANUAL)

# ================== SIDEBAR E FILTROS ==================
st.sidebar.title("Filtros")

grupos_disponiveis = sorted(comparativo_df["Grupo"].dropna().unique().tolist())
opcoes_filtro = ["Todas"] + grupos_disponiveis

selecao_grupos = st.sidebar.multiselect(
    "Selecione uma ou mais cooperativas:",
    options=opcoes_filtro,
    default=["Todas"]
)

if not selecao_grupos:
    st.sidebar.warning("Selecione pelo menos uma cooperativa.")
    comparativo_filtrado_df = comparativo_df.iloc[0:0]
    niveis_filtrado_df = niveis_df.iloc[0:0]
    financeiro_filtrado_df = financeiro_df.iloc[0:0]
    texto_selecao = "Nenhuma"

elif "Todas" in selecao_grupos or len(selecao_grupos) == len(grupos_disponiveis):
    comparativo_filtrado_df = comparativo_df.copy()
    niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == "TOTAL"].copy()
    financeiro_filtrado_df = financeiro_df.copy()
    texto_selecao = "Todas"

else:
    grupos_para_filtrar = selecao_grupos
    
    comparativo_filtrado_df = comparativo_df[comparativo_df["Grupo"].isin(grupos_para_filtrar)].copy()
    financeiro_filtrado_df = financeiro_df[financeiro_df["Grupo"].isin(grupos_para_filtrar)].copy()

    niveis_partial_df = niveis_df[niveis_df["Grupo"].isin(grupos_para_filtrar)].copy()
    niveis_filtrado_df = niveis_partial_df.groupby("Nível")[["Qtd Inicial", "Qtd Final"]].sum().reset_index()
    niveis_filtrado_df["Grupo"] = "Seleção" 
    
    if len(grupos_para_filtrar) > 3:
        texto_selecao = f"{len(grupos_para_filtrar)} cooperativas"
    else:
        texto_selecao = ", ".join(grupos_para_filtrar)


# --------- DATA DE ATUALIZAÇÃO (MANUAL) E LOGO ---------

_, col_right = st.columns([3, 1]) 

with col_right:
    col_text, col_logo = st.columns([2, 1])
    
    with col_text:
        st.markdown(
            f"""
            <div style='text-align: right;'>
                <span style='font-size: 16px; font-weight: bold; color: #084074;'>{DATA_MANUAL}</span>
                <br>
                <span style='font-size: 13px; color: #366093;'>Data de Atualização</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_logo:
        try:
            st.image("sebrae.png", width=90)
        except Exception as e:
            pass 


# --------- KPIs ---------
status_df_filtrado = status_df.copy()

total_grupos = status_df_filtrado["COOPERATIVA"].nunique()
total_clientes = status_df_filtrado["Quantidade de clientes"].sum()
total_finalizados = status_df_filtrado["Finalizados"].sum()
consultorias_canceladas = 73
percentual_conclusao = (100 * total_finalizados / total_clientes) if total_clientes else 0

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.markdown(f'<div class="card"><div class="kpi-label">Cooperativas</div><div class="kpi-value">{total_grupos}</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="card"><div class="kpi-label">Total de clientes</div><div class="kpi-value">{total_clientes}</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="card"><div class="kpi-label">Atend. finalizados</div><div class="kpi-value">{total_finalizados}</div></div>', unsafe_allow_html=True)
with k4: st.markdown(f'<div class="card"><div class="kpi-label">Consultorias canceladas</div><div class="kpi-value kpi-value-cancel">{consultorias_canceladas}</div></div>', unsafe_allow_html=True)
with k5: st.markdown(f'<div class="card"><div class="kpi-label">Conclusão dos atendimentos</div><div class="kpi-value kpi-value-pend">{percentual_conclusao:.1f}%</div></div>', unsafe_allow_html=True)

# ---------- ABAS ----------
tab_geral, tab_canceladas, tab_comparativo, tab_perfil, tab_detalhes = st.tabs(
    ["Visão Geral", "Detalhe Canceladas", "Análise Comparativa por Grupo", "Análise por Perfil", "Dados Detalhados"]
)

# ==============================================================
# ---------------- TAB 1 - VISÃO GERAL -------------------------
# ==============================================================

with tab_geral:

    st.header("Análise Geral")
    st.subheader(f"Cooperativa selecionada: {texto_selecao}") 
    
    col1, col2, col3 = st.columns(3)
    media_inicial = comparativo_filtrado_df["Pontuação Inicial"].mean()
    media_final   = comparativo_filtrado_df["Pontuação Final"].mean()
    total_produtores = comparativo_filtrado_df.shape[0]

    with col1: 
        st.markdown(f'<div class="card"><div class="kpi-label">Total de produtores</div><div class="kpi-value">{total_produtores}</div></div>', unsafe_allow_html=True)
    with col2: 
        st.markdown(f'<div class="card"><div class="kpi-label">Pontuação Média Inicial</div><div class="kpi-value">{media_inicial:.2f}</div></div>', unsafe_allow_html=True)
    with col3: 
        st.markdown(f'<div class="card"><div class="kpi-label">Pontuação Média Final</div><div class="kpi-value">{media_final:.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---") 
    
    if not niveis_filtrado_df.empty:
        niveis_filtrado_df["Nível"] = pd.Categorical(
            niveis_filtrado_df["Nível"], categories=NIVEIS_ORDER, ordered=True
        )
        niveis_chart_df = niveis_filtrado_df.melt(
            id_vars=["Grupo", "Nível"],
            value_vars=["Qtd Inicial", "Qtd Final"],
            var_name="Tipo",
            value_name="Quantidade"
        )
        fig_niveis = px.bar(
            niveis_chart_df,
            x="Nível",
            y="Quantidade",
            color="Tipo",
            text="Quantidade",
            barmode="group",
            title=f"Distribuição de Níveis - {texto_selecao}",
            labels={"Quantidade": "Nr. Participantes"},
            color_discrete_map=mapa_cores_evolucao,
            category_orders={"Nível": NIVEIS_ORDER}
        )
        fig_niveis.update_traces(
            texttemplate='%{text:.0f}',
            textposition='auto'
        )
        fig_niveis.update_yaxes(showgrid=False)
        fig_niveis.update_xaxes(tickfont=dict(weight='bold'))
        fig_niveis.update_layout(
            height=500,
            title_font_size=20
        )
        fig_niveis = style_fig(fig_niveis)
        st.plotly_chart(fig_niveis)
    else:
        st.info("Nenhum dado de nível para a seleção atual.")


# ==============================================================
# ---------------- TAB 2 - DETALHE CANCELADAS -----------------
# ==============================================================

with tab_canceladas:
    st.header("Detalhe das Consultorias Canceladas")
    st.write("Distribuição de quantas etapas foram concluídas antes do cancelamento.")

    if not canceladas_df.empty and "COOPERATIVA" in canceladas_df.columns:
        plot_df = canceladas_df[canceladas_df['COOPERATIVA'].str.upper() != 'TOTAL'].copy()
        
        colunas_encontros = ["1 Encontro realizado", "2 Encontros realizados", "3 Encontros realizados", "4 Encontros realizados"]
        colunas_encontros_existentes = [col for col in colunas_encontros if col in plot_df.columns]

        if colunas_encontros_existentes:
            melted_df = plot_df.melt(id_vars="COOPERATIVA", value_vars=colunas_encontros_existentes, var_name="Etapa", value_name="Quantidade")
            melted_df = melted_df[melted_df["Quantidade"] > 0]
            
            if not melted_df.empty:
                if "TOTAL" in plot_df.columns:
                    plot_df = plot_df.sort_values(by="TOTAL", ascending=True)
                
                fig_cancel = px.bar(
                    melted_df, 
                    x="Quantidade", 
                    y="COOPERATIVA", 
                    color="Etapa", 
                    orientation='h', 
                    barmode='stack', 
                    title="Consultorias Canceladas por Etapa Concluída",
                    category_orders={"COOPERATIVA": plot_df["COOPERATIVA"].tolist()}, 
                    text="Quantidade"
                )
                
                # Texto deitado (0 graus) e centralizado
                fig_cancel.update_traces(
                    textposition='inside', 
                    textfont=dict(weight='bold'),
                    texttemplate='%{text:.0f}',
                    textangle=0,
                    insidetextanchor='middle' 
                )
                
                fig_cancel.update_xaxes(showgrid=False)
                fig_cancel = style_fig(fig_cancel)
                st.plotly_chart(fig_cancel, use_container_width=True)
            else:
                st.info("Não há dados de cancelamento por etapas para exibir.")
        else:
            st.warning("Colunas de encontros ('1 Encontro realizado', etc.) não encontradas na aba 'canceladas_detalhe'.")

        st.subheader("Ranking de Cancelamentos")
        
        if "TOTAL" in canceladas_df.columns:
            canceladas_df["TOTAL"] = pd.to_numeric(canceladas_df["TOTAL"], errors='coerce').fillna(0)
            ranked_canceladas_df = canceladas_df.sort_values(by="TOTAL", ascending=True)
            
            fig_ranking = px.bar(
                ranked_canceladas_df[ranked_canceladas_df["TOTAL"] > 0],
                x="TOTAL",
                y="COOPERATIVA",
                orientation='h',
                text="TOTAL",
                title="Total de Cancelamentos por Cooperativa",
                color_discrete_sequence=[cor_grafico_principal]
            )
            fig_ranking.update_traces(
                textposition='outside',
                textfont=dict(weight='bold')
            )
            fig_ranking.update_xaxes(showgrid=False)
            fig_ranking.update_yaxes(title=None) 
            fig_ranking = style_fig(fig_ranking)
            st.plotly_chart(fig_ranking, use_container_width=True)

        else:
            st.warning("Coluna 'TOTAL' não encontrada.")

        with st.expander("Ver Dados Brutos"):
            st.dataframe(canceladas_df)

    else:
        st.warning("Não foi possível carregar os dados de cancelamento. Verifique a aba 'canceladas_detalhe' no Excel.")

# ==============================================================
# ---------------- TAB 3 - COMPARATIVO -------------------------
# ==============================================================

with tab_comparativo:
    # --- GRÁFICO 1: CONHECIMENTO (PONTUAÇÃO) ---
    st.header("Comparativo de Pontuação Média (Conhecimento)")
    st.subheader(f"Exibindo resultados para: {texto_selecao}")

    participant_counts = comparativo_filtrado_df["Grupo"].value_counts()
    
    pontuacao_por_grupo_df = comparativo_filtrado_df.groupby("Grupo")[["Pontuação Inicial", "Pontuação Final"]].mean().reset_index()
    pontuacao_por_grupo_df["Evolução"] = pontuacao_por_grupo_df["Pontuação Final"] - pontuacao_por_grupo_df["Pontuação Inicial"]
    
    pontuacao_por_grupo_df["Participantes"] = pontuacao_por_grupo_df["Grupo"].apply(lambda g: participant_counts.get(g,0))
    
    # ================== REINSERIDA A OPÇÃO 'EVOLUÇÃO DETALHADA' ==================
    escolha = st.radio(
        "Selecione:", 
        ["Pontuação Final", "Pontuação Inicial", "Evolução", "Evolução Detalhada (Inicial vs. Final)", "Ambas"], 
        horizontal=True, 
        key='pontuacao_radio'
    )
    # ================== FIM ==================

    if not pontuacao_por_grupo_df.empty:
        if escolha == "Ambas":
            pontuacao_por_grupo_df.sort_values(by="Pontuação Final", ascending=True, inplace=True)
            
            melt = pontuacao_por_grupo_df.melt(
                id_vars=["Grupo", "Participantes"], 
                value_vars=["Pontuação Inicial", "Pontuação Final"], 
                var_name="Tipo", 
                value_name="Valor"
            )
            
            fig = px.bar(
                melt, 
                x="Valor", 
                y="Grupo", 
                color="Tipo", 
                orientation='h', 
                barmode="group", 
                color_discrete_map=mapa_cores_evolucao, 
                title="Conhecimento: Inicial vs. Final", 
                labels={'Valor': "Média da Pontuação", "Grupo": "Cooperativa"}, 
                text_auto='.2f',
                hover_data=["Participantes"]
            )
            fig.update_xaxes(showgrid=False)

        # ================== BLOCO REINSERIDO: GRÁFICO DE HALTERES PARA CONHECIMENTO ==================
        elif escolha == "Evolução Detalhada (Inicial vs. Final)":
            chart_data = pontuacao_por_grupo_df.sort_values(by="Pontuação Final", ascending=True)
            
            fig = go.Figure()

            # Bolinha Inicial
            fig.add_trace(go.Scatter(
                x=chart_data["Pontuação Inicial"],
                y=chart_data["Grupo"],
                mode='markers+text', 
                text=chart_data["Pontuação Inicial"].apply(lambda x: f"{x:.2f}"), 
                textposition='middle left', 
                textfont=dict(color='black', weight='bold'), 
                name='Nota Inicial',
                marker=dict(color='#6AA4D9', size=10),
                customdata=chart_data["Participantes"],
                hovertemplate='<b>%{y}</b><br>Inicial: %{x:.2f}<br>Participantes: %{customdata}<extra></extra>'
            ))

            # Bolinha Final
            fig.add_trace(go.Scatter(
                x=chart_data["Pontuação Final"],
                y=chart_data["Grupo"],
                mode='markers+text', 
                text=chart_data["Pontuação Final"].apply(lambda x: f"{x:.2f}"), 
                textposition='middle right', 
                textfont=dict(color='black', weight='bold'), 
                name='Nota Final',
                marker=dict(color='#084074', size=14),
                customdata=chart_data["Participantes"],
                hovertemplate='<b>%{y}</b><br>Final: %{x:.2f}<br>Participantes: %{customdata}<extra></extra>'
            ))

            for i, row in chart_data.iterrows():
                fig.add_shape(
                    type="line",
                    x0=row["Pontuação Inicial"], y0=row["Grupo"],
                    x1=row["Pontuação Final"], y1=row["Grupo"],
                    line=dict(color="gray", width=1)
                )

            fig.update_layout(
                title="Pontuação Inicial vs. Final (Detalhado)",
                xaxis_title="Média de Pontuação",
                yaxis_title="Cooperativa",
                height=600,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(color="black")
            )
            
            fig.update_xaxes(showgrid=False, tickfont=dict(color='black', weight='bold'))
            fig.update_yaxes(showgrid=False, tickfont=dict(color='black', weight='bold'))
            
            # Sem borda manual (o style_fig cuida disso)
            fig = style_fig(fig)
            st.plotly_chart(fig, use_container_width=True)
        # ================== FIM DO BLOCO REINSERIDO ==================

        else:
            dados_plot = pontuacao_por_grupo_df.sort_values(by=escolha, ascending=True)
            fig = px.bar(
                dados_plot, 
                x=escolha, 
                y="Grupo", 
                orientation='h', 
                title=f"Ranking de {escolha} (Conhecimento)", 
                labels={escolha: "Pontuação", "Grupo": "Cooperativa"}, 
                text_auto='.2f', 
                color_discrete_sequence=[cor_grafico_principal],
                hover_data=["Participantes"]
            )
            
            if escolha == "Evolução":
                media_geral = (comparativo_filtrado_df["Pontuação Final"] - comparativo_filtrado_df["Pontuação Inicial"]).mean()
            else:
                media_geral = comparativo_filtrado_df[escolha].mean()

            fig.add_vline(x=media_geral, line_width=2, line_dash="dash", line_color="#F2E77F", annotation_text=f"Média: {media_geral:.1f}")
            fig.update_xaxes(showgrid=False) 

        if escolha != "Evolução Detalhada (Inicial vs. Final)":
            fig = style_fig(fig)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de pontuação para a seleção atual.")
    
    st.markdown("---")

    # --- GRÁFICO 2: ADESÃO À TRILHA ---
    st.header("Análise do bloco de Gestão Financeira da Trilha de adesão")
    st.markdown("Este bloco analisa o **engajamento e a execução** das funcionalidades do bloco de gestão financeira.")
    
    adesao_grupos_df = financeiro_filtrado_df[financeiro_filtrado_df["Grupo"] != "TOTAL"].copy()
    adesao_grupos_df["Participantes"] = adesao_grupos_df["Grupo"].apply(lambda g: participant_counts.get(g,0))
    
    if not adesao_grupos_df.empty:
        if 'Evolução Absoluta' in adesao_grupos_df.columns and "Soma Final" in adesao_grupos_df.columns:
            adesao_grupos_df["Soma Final"].fillna(adesao_grupos_df['Evolução Absoluta'], inplace=True)
        if 'Soma Inicial' in adesao_grupos_df.columns and 'Soma Inicial (todos)' in adesao_grupos_df.columns:
            adesao_grupos_df['Soma Inicial'].fillna(adesao_grupos_df['Soma Inicial (todos)'], inplace=True)
        
        adesao_grupos_df["Ganho de Adesão"] = adesao_grupos_df["Soma Final"] - adesao_grupos_df["Soma Inicial"]

        escolha_adesao = st.radio(
            "Selecione:", 
            ('Pontuação Final (Acumulado)', 'Evolução (Ganho)', 'Evolução Detalhada (Inicial vs. Final)'), 
            horizontal=True, 
            key='adesao_radio'
        )
        
        if escolha_adesao == 'Pontuação Final (Acumulado)':
            dados_plot = adesao_grupos_df.sort_values(by="Soma Final", ascending=True)
            fig_adesao = px.bar(
                dados_plot, 
                x="Soma Final", 
                y="Grupo", 
                orientation='h',
                title="Panorama de Adesão Final (Pontuação Acumulada)",
                labels={"Soma Final": "Pontos de Adesão", "Grupo": "Cooperativa"},
                text="Soma Final",
                color_discrete_sequence=[cor_grafico_principal],
                hover_data=["Participantes"]
            )
            fig_adesao.update_traces(
                textposition='inside', 
                textfont=dict(weight='bold'),
                texttemplate='%{text:.0f}',
                textangle=0,
                insidetextanchor='middle'
            )
            fig_adesao.update_xaxes(showgrid=False)
            fig_adesao = style_fig(fig_adesao)
            st.plotly_chart(fig_adesao, use_container_width=True)

        elif escolha_adesao == 'Evolução (Ganho)':
            dados_plot = adesao_grupos_df.sort_values(by="Ganho de Adesão", ascending=True)
            fig_adesao = px.bar(
                dados_plot, 
                x="Ganho de Adesão", 
                y="Grupo", 
                orientation='h',
                title="Evolução (Pontos Ganhos durante a Consultoria)",
                labels={"Ganho de Adesão": "Novos Pontos Conquistados", "Grupo": "Cooperativa"},
                text="Ganho de Adesão",
                color_discrete_sequence=[cor_grafico_principal], 
                hover_data=["Participantes"]
            )
            
            fig_adesao.update_traces(
                textposition='inside', 
                textfont=dict(weight='bold'),
                texttemplate='%{text:.0f}',
                textangle=0,
                insidetextanchor='middle'
            )
            
            media_esforco = adesao_grupos_df["Ganho de Adesão"].mean()
            fig_adesao.add_vline(x=media_esforco, line_width=2, line_dash="dash", line_color="#F2E77F", annotation_text=f"Média: {media_esforco:.0f}")
            
            fig_adesao.update_xaxes(showgrid=False)
            fig_adesao = style_fig(fig_adesao)
            st.plotly_chart(fig_adesao, use_container_width=True)

        elif escolha_adesao == 'Evolução Detalhada (Inicial vs. Final)':
            chart_data = adesao_grupos_df.sort_values(by="Soma Final", ascending=True)
            
            fig_adesao = go.Figure()

            fig_adesao.add_trace(go.Scatter(
                x=chart_data["Soma Inicial"],
                y=chart_data["Grupo"],
                mode='markers+text', 
                text=chart_data["Soma Inicial"].apply(lambda x: f"{x:.0f}"), 
                textposition='middle left', 
                textfont=dict(color='black', weight='bold'), 
                name='Adesão Inicial',
                marker=dict(color='#6AA4D9', size=10),
                customdata=chart_data["Participantes"],
                hovertemplate='<b>%{y}</b><br>Inicial: %{x:.0f}<br>Participantes: %{customdata}<extra></extra>'
            ))

            fig_adesao.add_trace(go.Scatter(
                x=chart_data["Soma Final"],
                y=chart_data["Grupo"],
                mode='markers+text', 
                text=chart_data["Soma Final"].apply(lambda x: f"{x:.0f}"), 
                textposition='middle right', 
                textfont=dict(color='black', weight='bold'), 
                name='Adesão Final',
                marker=dict(color='#084074', size=14),
                customdata=chart_data["Participantes"],
                hovertemplate='<b>%{y}</b><br>Final: %{x:.0f}<br>Participantes: %{customdata}<extra></extra>'
            ))

            for i, row in chart_data.iterrows():
                fig_adesao.add_shape(
                    type="line",
                    x0=row["Soma Inicial"], y0=row["Grupo"],
                    x1=row["Soma Final"], y1=row["Grupo"],
                    line=dict(color="gray", width=1)
                )

            fig_adesao.update_layout(
                title="Pontuação Inicial vs. Final",
                xaxis_title="Pontos de Adesão",
                yaxis_title="Cooperativa",
                height=600,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(color="black")
            )
            
            # Remove a grade e garante fonte preta, SEM borda manual extra
            fig_adesao.update_xaxes(showgrid=False, tickfont=dict(color='black', weight='bold'))
            fig_adesao.update_yaxes(showgrid=False, tickfont=dict(color='black', weight='bold'))
            
            # A borda agora vem apenas da função style_fig
            fig_adesao = style_fig(fig_adesao)
            st.plotly_chart(fig_adesao, use_container_width=True)

    else:
        st.info("Nenhum dado de adesão (trilha) disponível para a seleção atual.")

# ==============================================================
# ---------------- TAB 4 - PERFIL ------------------------------
# ==============================================================

with tab_perfil:
    st.header("Análise de Perfil dos Produtores")
    st.write(f"Analisando o perfil para o grupo: **{texto_selecao}**") 
    perguntas_analise = ['TEM SUCESSÃO FAMILIAR? (JOVENS INSERIDOS NO NEGÓCIO)', 'TEM MULHER NA GESTÃO DA PROPRIEDADE?', 'A PROPRIEDADE TRABALHA COM', 'Potencial para um nível 2 de trabalho?']
    pergunta_selecionada = st.selectbox("Escolha uma característica do perfil para analisar:", perguntas_analise)
    perguntas_especiais = ['Potencial para um nível 2 de trabalho?', 'TEM MULHER NA GESTÃO DA PROPRIEDADE?', 'TEM SUCESSÃO FAMILIAR? (JOVENS INSERIDOS NO NEGÓCIO)']
    if pergunta_selecionada in perguntas_especiais:
        st.subheader(f"Análise Específica: {pergunta_selecionada}")
        analise_especial_df = comparativo_filtrado_df.dropna(subset=[pergunta_selecionada, 'Nível Final'])
        if analise_especial_df[pergunta_selecionada].dtype == 'object':
            analise_especial_df = analise_especial_df[analise_especial_df[pergunta_selecionada].astype(str).str.strip() != '']
            analise_especial_df = analise_especial_df[analise_especial_df[pergunta_selecionada] != 'nan']
        if not analise_especial_df.empty:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                contagem_respostas = analise_especial_df[pergunta_selecionada].value_counts()
                fig_pie = px.pie(values=contagem_respostas.values, names=contagem_respostas.index, title="Distribuição das Respostas", hole=.3, color_discrete_sequence=cores_principais)
                fig_pie.update_traces(textinfo='percent+label', textfont_size=14)
                fig_pie = style_fig(fig_pie)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                analise_especial_df["Nível Final"] = pd.Categorical(analise_especial_df["Nível Final"], categories=NIVEIS_ORDER, ordered=True)
                niveis_por_resposta = analise_especial_df.groupby([pergunta_selecionada, 'Nível Final']).size().reset_index(name='Contagem')
                niveis_por_resposta.sort_values(by="Nível Final", inplace=True)
                fig_niveis_resp = px.bar(niveis_por_resposta, x='Nível Final', y='Contagem', color=pergunta_selecionada, barmode='group', title="Distribuição do Nível Final por Resposta", labels={'Contagem': 'Nr. de Produtores', 'Nível Final': 'Nível Final'}, category_orders={"Nível Final": NIVEIS_ORDER}, color_discrete_map=mapa_cores_sim_nao)
                fig_niveis_resp.update_traces(texttemplate='%{y}', textposition='outside')
                fig_niveis_resp.update_yaxes(showgrid=False) 
                fig_niveis_resp = style_fig(fig_niveis_resp)
                st.plotly_chart(fig_niveis_resp, use_container_width=True)
        else:
            st.warning(f"Não há dados suficientes para a análise de '{pergunta_selecionada}' neste grupo.")
    else:
        st.subheader(f"Distribuição de Respostas para: {pergunta_selecionada}")
        analise_df = comparativo_filtrado_df.dropna(subset=[pergunta_selecionada])
        if analise_df[pergunta_selecionada].dtype == 'object':
            analise_df = analise_df[analise_df[pergunta_selecionada].astype(str).str.strip() != '']
            analise_df = analise_df[analise_df[pergunta_selecionada] != 'nan']
        if not analise_df.empty:
            counts = analise_df[pergunta_selecionada].value_counts()
            percentages = analise_df[pergunta_selecionada].value_counts(normalize=True) * 100
            summary_df = pd.DataFrame({'Resposta': counts.index, 'Contagem': counts.values, 'Porcentagem': percentages.values})
            summary_df = summary_df.sort_values(by='Contagem', ascending=True)
            fig_perfil = px.bar(summary_df, x='Contagem', y='Resposta', orientation='h', title=f'Distribuição de Respostas para: "{pergunta_selecionada}"', text=summary_df['Porcentagem'].apply(lambda p: f'{p:.1f}%'))
            fig_perfil.update_traces(textposition='outside', marker_color=cores_principais[0])
            fig_perfil.update_layout(yaxis_title="Respostas", xaxis_title="Número de Respostas")
            fig_perfil.update_xaxes(showgrid=False)
            fig_perfil = style_fig(fig_perfil)
            st.plotly_chart(fig_perfil, use_container_width=True)
        else:
            st.warning(f"Não há dados para a pergunta '{pergunta_selecionada}' neste grupo.")
            
# ==============================================================
# ---------------- TAB 5 - DETALHES ----------------------------
# ==============================================================

with tab_detalhes:
    st.header("Detalhes por Participante")
    st.subheader(f"Exibindo participantes de: {texto_selecao}") 
    st.dataframe(comparativo_filtrado_df)