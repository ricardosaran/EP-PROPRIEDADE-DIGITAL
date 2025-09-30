import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# Configuração da página
st.set_page_config(layout="wide")

# Título do Dashboard
st.title("Painel de Análise de Resultados")

# Carregamento dos dados a partir do arquivo Excel
@st.cache_data
def load_data():
    excel_file_path = "master_resultados.xlsx"
    comparativo_df = pd.read_excel(excel_file_path, sheet_name="comparativo_master")
    niveis_df = pd.read_excel(excel_file_path, sheet_name="niveis_master")
    financeiro_df = pd.read_excel(excel_file_path, sheet_name="financeiro_master")
    return comparativo_df, niveis_df, financeiro_df

try:
    comparativo_df, niveis_df, financeiro_df = load_data()

    # Sidebar para filtros
    st.sidebar.title("Filtros")
    if "Grupo" in comparativo_df.columns:
        grupos_disponiveis = sorted(comparativo_df["Grupo"].dropna().unique().tolist())
        grupo_selecionado = st.sidebar.selectbox("Selecione um Grupo", ["Todos"] + grupos_disponiveis)
    else:
        st.error("A coluna 'Grupo' não foi encontrada na planilha 'comparativo_master'.")
        st.stop()

    # Filtrando os dados
    if grupo_selecionado != "Todos":
        comparativo_filtrado_df = comparativo_df[comparativo_df["Grupo"] == grupo_selecionado]
        niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == grupo_selecionado]
    else:
        comparativo_filtrado_df = comparativo_df
        niveis_filtrado_df = niveis_df[niveis_df["Grupo"] == "TOTAL"]

    # --- Análise Geral ---
    st.header("Análise Geral")
    col1, col2, col3 = st.columns(3)
    media_inicial = comparativo_filtrado_df['Pontuação Inicial'].mean()
    media_final = comparativo_filtrado_df['Pontuação Final'].mean()
    valor_media_inicial = f"{media_inicial:.2f}" if pd.notna(media_inicial) else "N/A"
    valor_media_final = f"{media_final:.2f}" if pd.notna(media_final) else "N/A"
    with col1:
        st.metric(label="Total de Participantes", value=comparativo_filtrado_df.shape[0])
    with col2:
        st.metric(label="Pontuação Média Inicial", value=valor_media_inicial)
    with col3:
        st.metric(label="Pontuação Média Final", value=valor_media_final)

    # --- Evolução dos Níveis ---
    st.header("Evolução dos Níveis")
    if not niveis_filtrado_df.empty:
        niveis_chart_df = niveis_filtrado_df.melt(id_vars=["Grupo", "Nível"],
                                                  value_vars=["Qtd Inicial", "Qtd Final"],
                                                  var_name="Tipo",
                                                  value_name="Quantidade")
        fig_niveis = px.bar(niveis_chart_df, x="Nível", y="Quantidade", color="Tipo", barmode="group",
                            title=f"Distribuição de Níveis - {grupo_selecionado}",
                            labels={"Quantidade": "Número de Participantes", "Nível": "Nível de Conhecimento", "Tipo": "Medição"},
                            text_auto=True) # Adicionado para mostrar valores nas barras
        st.plotly_chart(fig_niveis, use_container_width=True)
    else:
        st.warning(f"Não há dados de 'Níveis' para o grupo '{grupo_selecionado}'.")

    # --- Análise Financeira ---
    st.header("Análise Financeira")

    # --- ATUALIZAÇÃO 1: BOTÕES DE SELEÇÃO ---
    escolha_financeiro = st.radio(
        "Selecione a visualização financeira:",
        ('Soma Final', 'Soma Inicial', 'Ambas'),
        horizontal=True
    )

    financeiro_grupos_df = financeiro_df[financeiro_df["Grupo"] != "TOTAL"].copy()
    
    # Preenchendo dados faltantes de forma inteligente
    coluna_soma_final = "Soma Final " if "Soma Final " in financeiro_grupos_df.columns else "Soma Final"
    if 'Evolução Absoluta' in financeiro_grupos_df.columns and coluna_soma_final in financeiro_grupos_df.columns:
        financeiro_grupos_df[coluna_soma_final].fillna(financeiro_grupos_df['Evolução Absoluta'], inplace=True)
    if 'Soma Inicial' in financeiro_grupos_df.columns and 'Soma Inicial (todos)' in financeiro_grupos_df.columns:
         financeiro_grupos_df['Soma Inicial'].fillna(financeiro_grupos_df['Soma Inicial (todos)'], inplace=True)

    fig_financeiro = None
    if escolha_financeiro == 'Soma Final':
        financeiro_grupos_df.dropna(subset=[coluna_soma_final], inplace=True)
        fig_financeiro = px.bar(financeiro_grupos_df, x="Grupo", y=coluna_soma_final,
                                title="Soma Final Financeira por Grupo",
                                labels={coluna_soma_final: "Soma Final", "Grupo": "Grupo"},
                                text_auto=True) # --- ATUALIZAÇÃO 2: NÚMEROS NAS BARRAS ---
    elif escolha_financeiro == 'Soma Inicial':
        financeiro_grupos_df.dropna(subset=['Soma Inicial'], inplace=True)
        fig_financeiro = px.bar(financeiro_grupos_df, x="Grupo", y='Soma Inicial',
                                title="Soma Inicial Financeira por Grupo",
                                labels={'Soma Inicial': "Soma Inicial", "Grupo": "Grupo"},
                                text_auto=True) # --- ATUALIZAÇÃO 2: NÚMEROS NAS BARRAS ---
    elif escolha_financeiro == 'Ambas':
        financeiro_melted_df = financeiro_grupos_df.melt(
            id_vars='Grupo',
            value_vars=['Soma Inicial', coluna_soma_final],
            var_name='Tipo de Soma',
            value_name='Valor'
        )
        financeiro_melted_df.dropna(subset=['Valor'], inplace=True)
        fig_financeiro = px.bar(financeiro_melted_df, x="Grupo", y='Valor', color='Tipo de Soma',
                                barmode='group',
                                title="Comparativo: Soma Inicial vs. Soma Final",
                                labels={'Valor': "Valor", "Grupo": "Grupo", "Tipo de Soma": "Tipo"},
                                text_auto=True) # --- ATUALIZAÇÃO 2: NÚMEROS NAS BARRAS ---

    if fig_financeiro:
        st.plotly_chart(fig_financeiro, use_container_width=True)
    else:
        st.warning("Não foi possível gerar o gráfico financeiro com os dados atuais.")


    # --- Detalhes por Participante ---
    st.header("Detalhes por Participante")
    st.dataframe(comparativo_filtrado_df)

except FileNotFoundError:
    st.error("Erro: Arquivo 'master_resultados.xlsx' não encontrado.")
    st.info("Por favor, verifique se o arquivo Excel está na mesma pasta que o script 'painel.py'.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao processar os dados.")
    st.warning(f"Detalhe do erro: {e}")
    st.info("Verifique se os nomes das planilhas (abas) e das colunas no seu arquivo Excel correspondem ao esperado pelo script.")