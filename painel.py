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

# ------------------- PALETA DE CORES -------------------
cores_principais = ['#2E6D4A', '#91BF59', '#F2E77F', '#252525']
mapa_cores_sim_nao = {'Sim': '#2E6D4A', 'Não': '#91BF59'}
mapa_cores_evolucao = {
    'Pontuação Inicial': '#91BF59',
    'Pontuação Final': '#2E6D4A',
    'Qtd Inicial': '#91BF59',
    'Qtd Final': '#2E6D4A',
    'Soma Inicial': '#91BF59',
    'Soma Final': '#2E6D4A'
}
NIVEIS_ORDER = ["Básico", "Intermediário", "Avançado"]

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

# --------- CARREGAMENTO DE DADOS ---------
@st.cache_data
def load_all_data():
    excel_file_path = "master_resultados.xlsx"
    comparativo_df = pd.read_excel(excel_file_path, sheet_name="comparativo_master")
    niveis_df = pd.read_excel(excel_file_path, sheet_name="niveis_master")
    financeiro_df = pd.read_excel(excel_file_path, sheet_name="financeiro_master")
    questionario_df = pd.read_excel(excel_file_path, sheet_name="questionario")
    status_df = pd.read_excel(excel_file_path, sheet_name="status_consultorias")

    for df in [comparativo_df, niveis_df, financeiro_df, questionario_df, status_df]:
        df.columns = df.columns.str.strip()

    for col in questionario_df.select_dtypes(include=['object']).columns:
      questionario_df[col] = questionario_df[col].astype(str).str.strip()

    questionario_df.rename(columns={'COOPERATIVA': 'Grupo', 'CLIENTE': 'Cliente'}, inplace=True)
    merged_df = pd.merge(comparativo_df, questionario_df, on=['Grupo', 'Cliente'], how='left')

    return merged_df, niveis_df, financeiro_df, status_df

# ATENÇÃO: Verifique se 'financeiro_df' está sendo retornado e atribuído
comparativo_df, niveis_df, financeiro_df, status_df = load_all_data()

# ---------- FILTRO LATERAL ÚNICO ----------
st.sidebar.title("Filtros")

grupos_disponiveis = sorted(comparativo_df["Grupo"].dropna().unique().tolist())
grupo_selecionado = st.sidebar.selectbox("Selecione uma cooperativa", ["Todas"] + grupos_disponiveis)

if grupo_selecionado != "Todas":
    comparativo_filtrado_df = comparativo_df[comparativo_df["Grupo"] == grupo_selecionado]
    niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == grupo_selecionado]
else:
    comparativo_filtrado_df = comparativo_df.copy()
    niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == "TOTAL"] if "TOTAL" in niveis_df["Grupo"].values else niveis_df.copy()

# ================== BLOCO MODIFICADO ==================
# --------- DATA DE ATUALIZAÇÃO E LOGO ---------
# O código agora identifica a data de modificação do arquivo Excel

# Define o caminho do arquivo (deve ser o mesmo da função load_all_data)
excel_file_path = "master_resultados.xlsx"
try:
    # Pega a data da última modificação do arquivo
    mod_time = os.path.getmtime(excel_file_path)
    update_time = datetime.fromtimestamp(mod_time)
    timestamp_str = update_time.strftime("%d/%m/%Y %H:%M:%S")
except FileNotFoundError:
    timestamp_str = "Arquivo não encontrado"

# Criar colunas para alinhar à direita (coluna da esquerda vazia)
_, col_right = st.columns([3, 1]) # Proporção 3:1 

with col_right:
    # Criar colunas internas para texto e logo
    col_text, col_logo = st.columns([2, 1]) # Proporção 2:1 para texto/logo
    
    with col_text:
        st.markdown(
            f"""
            <div style='text-align: right;'>
                <span style='font-size: 16px; font-weight: bold; color: #084074;'>{timestamp_str}</span>
                <br>
                <span style='font-size: 13px; color: #366093;'>Data de Atualização</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_logo:
        try:
            # AVISO: Você precisa ter um arquivo 'logo.png' (ou o nome correto)
            # na mesma pasta do seu script .py
            st.image("sebrae.png", width=90)
        except Exception as e:
            pass # Não mostra nada se o logo falhar
# ================== FIM DO BLOCO MODIFICADO ==================


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
tab_geral, tab_comparativo, tab_perfil, tab_detalhes = st.tabs(
    ["Visão Geral", "Análise Comparativa por Grupo", "Análise por Perfil", "Dados Detalhados"]
)

# ==============================================================
# ---------------- TAB 1 - VISÃO GERAL -------------------------
# ==============================================================

with tab_geral:

    st.header("Análise Geral")
    st.subheader(f"Cooperativa selecionado: {grupo_selecionado}")
    
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
    
    st.markdown("---") # Adiciona uma linha horizontal para separar
    
    # ---------------- Gráfico de Níveis ----------------
    
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
            title=f"Distribuição de Níveis - {grupo_selecionado}",
            labels={"Quantidade": "Nr. Participantes"},
            color_discrete_map=mapa_cores_evolucao,
            category_orders={"Nível": NIVEIS_ORDER}
        )

        fig_niveis.update_traces(
            texttemplate='%{text:.0f}', # Formata como número inteiro
            textposition='auto'        # Posição automática (dentro/fora, cor auto)
        )
        
        # Remove as linhas de grade do eixo Y (fundo)
        fig_niveis.update_yaxes(showgrid=False)
        
        # Coloca os rótulos do eixo X em negrito
        fig_niveis.update_xaxes(tickfont=dict(weight='bold'))
        
        # Define uma altura fixa para evitar o "esticado"
        # e aumenta o tamanho da fonte do título
        fig_niveis.update_layout(
            height=500,  # Altura fixa de 500px
            title_font_size=20 # Tamanho da fonte do título
        )
        
        fig_niveis = style_fig(fig_niveis)
        
        # Removido 'use_container_width=True' para que o gráfico
        # use seu tamanho padrão e não estique mais.
        st.plotly_chart(fig_niveis)

# ==============================================================
# ---------------- TAB 2 - COMPARATIVO -------------------------
# ==============================================================

with tab_comparativo:
    st.header("Comparativo de Pontuação Média por Grupo")

    participant_counts = comparativo_df["Grupo"].value_counts()

    pontuacao_por_grupo_df = comparativo_df.groupby("Grupo")[["Pontuação Inicial", "Pontuação Final"]]\
                                           .mean()\
                                           .reset_index()

    pontuacao_por_grupo_df["Grupo_com_contagem"] = pontuacao_por_grupo_df["Grupo"].apply(
        lambda g: f"{g} (N={participant_counts.get(g,0)})"
    )

    escolha = st.radio("Selecione:", ["Pontuação Final", "Pontuação Inicial", "Ambas"], horizontal=True, key='pontuacao_radio')

    if escolha == "Ambas":
        melt = pontuacao_por_grupo_df.melt(
            id_vars=["Grupo", "Grupo_com_contagem"],
            value_vars=["Pontuação Inicial", "Pontuação Final"],
            var_name="Tipo",
            value_name="Valor"
        )

        fig = px.bar(
            melt, x="Grupo_com_contagem", y="Valor", color="Tipo",
            barmode="group", color_discrete_map=mapa_cores_evolucao,
            title="Comparativo: Pontuação Média Inicial vs. Final",
            labels={'Valor': "Média da Pontuação", "Grupo_com_contagem": "Grupo", "Tipo": "Tipo"},
            text_auto='.2f'
        )
    else:
        fig = px.bar(
            pontuacao_por_grupo_df,
            x="Grupo_com_contagem",
            y=escolha,
            title=f"Pontuação Média ({escolha}) por Grupo",
            labels={escolha: "Pontuação Média", "Grupo_com_contagem": "Grupo"},
            text_auto='.2f',
            color_discrete_sequence=[cores_principais[0] if escolha=="Pontuação Final" else cores_principais[1]]
        )

    fig.update_yaxes(showgrid=False) # Remove linhas de fundo
    
    fig = style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)
    
    st.header("Análise Financeira")
    financeiro_grupos_df = financeiro_df[financeiro_df["Grupo"] != "TOTAL"].copy()
    financeiro_grupos_df['Grupo_com_contagem'] = financeiro_grupos_df['Grupo'].apply(lambda grupo: f"{grupo} (N={participant_counts.get(grupo, 0)})")
    
    escolha_financeiro = st.radio("Selecione a visualização financeira:", ('Soma Final', 'Soma Inicial', 'Ambas'), horizontal=True, key='financeiro_radio')
    
    coluna_soma_final = "Soma Final"
    if 'Evolução Absoluta' in financeiro_grupos_df.columns and coluna_soma_final in financeiro_grupos_df.columns:
        financeiro_grupos_df[coluna_soma_final].fillna(financeiro_grupos_df['Evolução Absoluta'], inplace=True)
    if 'Soma Inicial' in financeiro_grupos_df.columns and 'Soma Inicial (todos)' in financeiro_grupos_df.columns:
        financeiro_grupos_df['Soma Inicial'].fillna(financeiro_grupos_df['Soma Inicial (todos)'], inplace=True)
    
    if escolha_financeiro == 'Ambas':
        financeiro_melted_df = financeiro_grupos_df.melt(id_vars=['Grupo', 'Grupo_com_contagem'], value_vars=['Soma Inicial', coluna_soma_final], var_name='Tipo de Soma', value_name='Valor')
        financeiro_melted_df.dropna(subset=['Valor'], inplace=True)
        fig_financeiro = px.bar(financeiro_melted_df, x="Grupo_com_contagem", y='Valor', color='Tipo de Soma', barmode='group', title="Comparativo: Soma Inicial vs. Soma Final", labels={'Valor': "Valor", "Grupo_com_contagem": "Grupo", "Tipo de Soma": "Tipo"}, text_auto=True, color_discrete_map=mapa_cores_evolucao)
    else:
        coluna_selecionada = 'Soma Final' if escolha_financeiro == 'Soma Final' else 'Soma Inicial'
        if coluna_selecionada in financeiro_grupos_df.columns:
            financeiro_grupos_df.dropna(subset=[coluna_selecionada], inplace=True)
            fig_financeiro = px.bar(financeiro_grupos_df, x="Grupo_com_contagem", y=coluna_selecionada, title=f"{coluna_selecionada} Financeira por Grupo", labels={coluna_selecionada: coluna_selecionada, "Grupo_com_contagem": "Grupo"}, text_auto=True, color_discrete_sequence=[cores_principais[0] if coluna_selecionada == 'Soma Final' else cores_principais[1]])
        else:
            fig_financeiro = None

    if fig_financeiro is not None:
        fig_financeiro.update_yaxes(showgrid=False) # Remove linhas de fundo
        fig_financeiro = style_fig(fig_financeiro)
        st.plotly_chart(fig_financeiro, use_container_width=True)


# ==============================================================
# ---------------- TAB 3 - PERFIL ------------------------------
# ==============================================================

with tab_perfil:
    st.header("Análise de Perfil dos Produtores")
    st.write(f"Analisando o perfil para o grupo: **{grupo_selecionado}**")
    
    perguntas_analise = [
        'TEM SUCESSÃO FAMILIAR? (JOVENS INSERIDOS NO NEGÓCIO)', 
        'TEM MULHER NA GESTÃO DA PROPRIEDADE?', 
        'A PROPRIEDADE TRABALHA COM', 
        'Potencial para um nível 2 de trabalho?'
    ]
    pergunta_selecionada = st.selectbox("Escolha uma característica do perfil para analisar:", perguntas_analise)
    
    perguntas_especiais = [
        'Potencial para um nível 2 de trabalho?', 
        'TEM MULHER NA GESTÃO DA PROPRIEDADE?', 
        'TEM SUCESSÃO FAMILIAR? (JOVENS INSERIDOS NO NEGÓCIO)'
    ]
    
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
                
                fig_niveis_resp.update_yaxes(showgrid=False) # Remove linhas de fundo
                
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
            
            # É 'update_xaxes' pois o gráfico é horizontal
            fig_perfil.update_xaxes(showgrid=False) # Remove linhas de fundo
            
            fig_perfil = style_fig(fig_perfil)
            st.plotly_chart(fig_perfil, use_container_width=True)
        else:
            st.warning(f"Não há dados para a pergunta '{pergunta_selecionada}' neste grupo.")
            
# ==============================================================
# ---------------- TAB 4 - DETALHES ----------------------------
# ==============================================================

with tab_detalhes:
    st.header("Detalhes por Participante")
    st.subheader(f"Exibindo participantes de: {grupo_selecionado}")
    st.dataframe(comparativo_filtrado_df)
