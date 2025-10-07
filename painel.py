# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import streamlit as st

# Plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Pacote 'plotly' não está instalado. Rode: pip install plotly")
    st.stop()

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

# ------------------- CONFIGURAÇÃO DA PÁGINA -------------------
st.set_page_config(layout="wide")

# ------------------- CSS (evitar cortes de borda) -------------------
st.markdown(
    """
    <style>
    .js-plotly-plot, .js-plotly-plot .plot-container, .js-plotly-plot .main-svg {
        overflow: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------- Helpers de estilo/borda Plotly -------------------
def add_plotly_border(fig: go.Figure, color: str = "#333", width: int = 2, pad: float = 0.004) -> go.Figure:
    x0, y0 = 0.0 + pad, 0.0 + pad
    x1, y1 = 1.0 - pad, 1.0 - pad
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
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
    add_plotly_border(fig, color=border_color, width=border_width, pad=pad)
    return fig

# ------------------- Título -------------------
st.title("Painel de Análise de Resultados")

# ------------------- Carregamento de dados -------------------
@st.cache_data
def load_data():
    excel_file_path = "master_resultados.xlsx"
    try:
        comparativo_df  = pd.read_excel(excel_file_path, sheet_name="comparativo_master")
        niveis_df       = pd.read_excel(excel_file_path, sheet_name="niveis_master")
        financeiro_df   = pd.read_excel(excel_file_path, sheet_name="financeiro_master")
        questionario_df = pd.read_excel(excel_file_path, sheet_name="questionario")
    except Exception as e:
        st.error(f"Erro ao carregar '{excel_file_path}'. Verifique as abas. Detalhe: {e}")
        st.stop()

    for df in [comparativo_df, niveis_df, financeiro_df, questionario_df]:
        df.columns = df.columns.str.strip()

    for col in questionario_df.select_dtypes(include=['object']).columns:
        questionario_df[col] = questionario_df[col].astype(str).str.strip()

    questionario_df.rename(columns={'COOPERATIVA': 'Grupo', 'CLIENTE': 'Cliente'}, inplace=True)
    merged_df = pd.merge(comparativo_df, questionario_df, on=['Grupo', 'Cliente'], how='left')
    return merged_df, niveis_df, financeiro_df

# ------------------- Leitura + Filtros -------------------
comparativo_df, niveis_df, financeiro_df = load_data()

st.sidebar.title("Filtros")
if "Grupo" in comparativo_df.columns:
    grupos_disponiveis = sorted(comparativo_df["Grupo"].dropna().unique().tolist())
    grupo_selecionado = st.sidebar.selectbox("Selecione um Grupo", ["Todos"] + grupos_disponiveis)
else:
    st.error("A coluna 'Grupo' não foi encontrada.")
    st.stop()

if grupo_selecionado != "Todos":
    comparativo_filtrado_df = comparativo_df[comparativo_df["Grupo"] == grupo_selecionado].copy()
    niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == grupo_selecionado]
else:
    comparativo_filtrado_df = comparativo_df.copy()
    niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == "TOTAL"]

# ------------------- Abas -------------------
tab_geral, tab_comparativo, tab_perfil, tab_detalhes = st.tabs(
    ["Visão Geral", "Análise Comparativa por Grupo", "Análise por Perfil", "Dados Detalhados"]
)

# =================== VISÃO GERAL ===================
with tab_geral:
    st.header("Análise Geral")
    st.subheader(f"Exibindo resultados para: {grupo_selecionado}")
    col1, col2, col3 = st.columns(3)
    media_inicial = comparativo_filtrado_df['Pontuação Inicial'].mean()
    media_final   = comparativo_filtrado_df['Pontuação Final'].mean()
    valor_media_inicial = f"{media_inicial:.2f}" if pd.notna(media_inicial) else "N/A"
    valor_media_final   = f"{media_final:.2f}"   if pd.notna(media_final)   else "N/A"
    with col1: st.metric(label="Total de Participantes", value=comparativo_filtrado_df.shape[0])
    with col2: st.metric(label="Pontuação Média Inicial", value=valor_media_inicial)
    with col3: st.metric(label="Pontuação Média Final", value=valor_media_final)
    st.header("Evolução dos Níveis")
    if not niveis_filtrado_df.empty:
        niveis_chart_df = niveis_filtrado_df.melt(id_vars=["Grupo", "Nível"], value_vars=["Qtd Inicial", "Qtd Final"], var_name="Tipo", value_name="Quantidade")
        fig_niveis = px.bar(niveis_chart_df, x="Nível", y="Quantidade", color="Tipo", barmode="group", title=f"Distribuição de Níveis - {grupo_selecionado}", labels={"Quantidade": "Nr. de Participantes", "Nível": "Nível de Conhecimento", "Tipo": "Medição"}, text_auto=True, color_discrete_map=mapa_cores_evolucao)
        fig_niveis = style_fig(fig_niveis)
        st.plotly_chart(fig_niveis, use_container_width=True)
    else:
        st.warning(f"Não há dados de 'Níveis' para o grupo '{grupo_selecionado}'.")

# =================== COMPARATIVO POR GRUPO ===================
with tab_comparativo:
    participant_counts = comparativo_df['Grupo'].value_counts()
    st.header("Comparativo de Pontuação Média por Grupo")
    pontuacao_por_grupo_df = comparativo_df.groupby('Grupo')[['Pontuação Inicial', 'Pontuação Final']].mean().reset_index()
    pontuacao_por_grupo_df['Grupo_com_contagem'] = pontuacao_por_grupo_df['Grupo'].apply(lambda grupo: f"{grupo} (N={participant_counts.get(grupo, 0)})")
    escolha_pontuacao = st.radio("Selecione a visualização de pontuação:", ('Pontuação Final', 'Pontuação Inicial', 'Ambas'), horizontal=True, key='pontuacao_radio')
    if escolha_pontuacao == 'Ambas':
        pontuacao_melted_df = pontuacao_por_grupo_df.melt(id_vars=['Grupo', 'Grupo_com_contagem'], value_vars=['Pontuação Inicial', 'Pontuação Final'], var_name='Tipo de Pontuação', value_name='Pontuação Média')
        fig_pontuacao = px.bar(pontuacao_melted_df, x="Grupo_com_contagem", y='Pontuação Média', color='Tipo de Pontuação', barmode='group', title="Comparativo: Pontuação Média Inicial vs. Final", labels={'Pontuação Média': "Média da Pontuação", "Grupo_com_contagem": "Grupo", "Tipo de Pontuação": "Tipo"}, text_auto='.2f', color_discrete_map=mapa_cores_evolucao)
    else:
        fig_pontuacao = px.bar(pontuacao_por_grupo_df, x="Grupo_com_contagem", y=escolha_pontuacao, title=f"Pontuação Média ({escolha_pontuacao}) por Grupo", labels={escolha_pontuacao: "Pontuação Média", "Grupo_com_contagem": "Grupo"}, text_auto='.2f', color_discrete_sequence=[cores_principais[0] if escolha_pontuacao == 'Pontuação Final' else cores_principais[1]])
    fig_pontuacao = style_fig(fig_pontuacao)
    st.plotly_chart(fig_pontuacao, use_container_width=True)
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
        fig_financeiro = style_fig(fig_financeiro)
        st.plotly_chart(fig_financeiro, use_container_width=True)

# =================== PERFIL ===================
with tab_perfil:
    st.header("Análise de Perfil dos Produtores")
    st.write(f"Analisando o perfil para o grupo: **{grupo_selecionado}**")
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
                niveis_por_resposta = analise_especial_df.groupby([pergunta_selecionada, 'Nível Final']).size().reset_index(name='Contagem')
                fig_niveis_resp = px.bar(niveis_por_resposta, x='Nível Final', y='Contagem', color=pergunta_selecionada, barmode='group', title="Distribuição do Nível Final por Resposta", labels={'Contagem': 'Nr. de Produtores', 'Nível Final': 'Nível Final'}, category_orders={"Nível Final": ["Básico", "Intermediário", "Avançado"]}, color_discrete_map=mapa_cores_sim_nao)
                fig_niveis_resp.update_traces(texttemplate='%{y}', textposition='outside')
                fig_niveis_resp = style_fig(fig_niveis_resp)
                st.plotly_chart(fig_niveis_resp, use_container_width=True)
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
            fig_perfil = style_fig(fig_perfil)
            st.plotly_chart(fig_perfil, use_container_width=True)

# =================== DETALHES ===================
with tab_detalhes:
    st.header("Detalhes por Participante")
    st.subheader(f"Exibindo participantes de: {grupo_selecionado}")
    st.dataframe(comparativo_filtrado_df)