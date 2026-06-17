import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página do Dashboard
st.set_page_config(page_title="Controle de Ocorrências", layout="wide")
st.title("📊 Painel de Controle de Faltas e Atrasos")

# 1. Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# Lista fixa dos seus 28 aprendizes e respectivas empresas para o formulário diário
lista_aprendizes_fixa = [f"Aprendiz {i}" for i in range(1, 29)]
lista_empresas_fixa = ["Ceratti", "Perfetti Van Melle", "Saint-Gobain", "Avery Dennison", "Duoflex"] * 5 + ["Ceratti", "Perfetti Van Melle", "Saint-Gobain"]

# Carrega o histórico de faltas/atrasos já existentes
try:
    df_historico = conn.read(ttl=0)
    if not df_historico.empty:
        df_historico["Data"] = df_historico["Data"].astype(str)
except Exception as e:
    df_historico = pd.DataFrame(columns=["Data", "Mês", "Ano", "Nome do Aprendiz", "Empresa", "Status", "Horário de Chegada", "Possui Atestado", "Link do Atestado"])

# 2. BARRA LATERAL - SELEÇÃO DA DATA ATUAL E FILTRO DE RELATÓRIO
st.sidebar.header("📅 Data do Registro")
data_selecionada = st.sidebar.date_input("Selecione o Dia de Hoje", datetime.now())
data_formatada = data_selecionada.strftime("%d/%m/%Y")
ano_atual = data_selecionada.year

lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
mes_atual_nome = lista_meses[data_selecionada.month - 1]

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Puxar Relatório Mensal")
mes_filtro = st.sidebar.selectbox("Escolha o mês para fechar com as empresas:", lista_meses, index=data_selecionada.month - 1)

# 3. PAINEL DE MÉTRICAS (Resumo do mês selecionado com base no histórico)
if not df_historico.empty:
    df_mes = df_historico[(df_historico["Mês"] == mes_filtro) & (df_historico["Ano"] == ano_atual)]
else:
    df_mes = pd.DataFrame()

col1, col2, col3 = st.columns(3)
with col1:
    total_faltas = len(df_mes[df_mes["Status"] == "Falta"]) if not df_mes.empty else 0
    st.metric(f"Total de Faltas ({mes_filtro})", total_faltas)
with col2:
    total_atrasos = len(df_mes[df_mes["Status"] == "Atraso"]) if not df_mes.empty else 0
    st.metric(f"Total de Atrasos ({mes_filtro})", total_atrasos)
with col3:
    total_atestados = len(df_mes[df_mes["Possui Atestado"] == "Sim"]) if not df_mes.empty else 0
    st.metric("Atestados Entregues", total_atestados)

st.markdown("---")
st.subheader(f"📝 Chamada do Dia: {data_formatada} ({mes_atual_nome})")
st.info("Deixe todos como 'Presente'. Mude para 'Falta' ou 'Atraso' apenas quem teve ocorrência. Só estes serão salvos na planilha!")

# 4. MONTAGEM DA TABELA DIÁRIA PARA EDIÇÃO
df_dia_formulario = pd.DataFrame({
    "Data": [data_formatada] * 28,
    "Mês": [mes_atual_nome] * 28,
    "Ano": [ano_atual] * 28,
    "Nome do Aprendiz": lista_aprendizes_fixa,
    "Empresa": lista_empresas_fixa,
    "Status": ["Presente"] * 28,
    "Horário de Chegada": ["-"] * 28,
    "Possui Atestado": ["Não"] * 28,
    "Link do Atestado": [""] * 28
}).sort_values(by=["Empresa", "Nome do Aprendiz"]).reset_index(drop=True)

# Se o usuário já salvou dados desse dia antes, puxa o que ele salvou para não perder
if not df_historico.empty:
    df_salvo_desse_dia = df_historico[df_historico["Data"] == data_formatada]
    if not df_salvo_desse_dia.empty:
        for idx, row in df_salvo_desse_dia.iterrows():
            df_dia_formulario.loc[df_dia_formulario["Nome do Aprendiz"] == row["Nome do Aprendiz"], ["Status", "Horário de Chegada", "Possui Atestado", "Link do Atestado"]] = [row["Status"], row["Horário de Chegada"], row["Possui Atestado"], row["Link do Atestado"]]

# Exibe o editor na tela organizado por Empresa
df_editado = st.data_editor(
    df_dia_formulario,
    hide_index=True,
    column_config={
        "Data": st.column_config.TextColumn("Data", disabled=True),
        "Mês": st.column_config.TextColumn("Mês", disabled=True),
        "Ano": st.column_config.NumberColumn("Ano", format="%d", disabled=True),
        "Nome do Aprendiz": st.column_config.TextColumn("Nome do Aprendiz", disabled=True),
        "Empresa": st.column_config.TextColumn("Empresa", disabled=True),
        "Status": st.column_config.SelectboxColumn("Status", options=["Presente", "Atraso", "Falta"], required=True),
        "Horário de Chegada": st.column_config.TextColumn("Horário de Chegada (HH:MM)"),
        "Possui Atestado": st.column_config.SelectboxColumn("Possui Atestado?", options=["Não", "Sim", "Não se aplica"]),
        "Link do Atestado": st.column_config.LinkColumn("Link do Atestado")
    },
    use_container_width=True
)

# 5. BOTÃO SALVAR (Filtra e joga na planilha apenas as Faltas e Atrasos)
if st.button("💾 Gravar Ocorrências na Planilha", type="primary"):
    try:
        # FILTRO INTELIGENTE: Remove quem está 'Presente'
        df_ocorrencias_novas = df_editado[df_editado["Status"].isin(["Falta", "Atraso"])]
        
        # Remove os registros antigos desse mesmo dia no histórico para não duplicar
        if not df_historico.empty:
            df_historico_limpo = df_historico[df_historico["Data"] != data_formatada]
        else:
            df_historico_limpo = pd.DataFrame()
            
        # Junta o histórico antigo com as novas ocorrências do dia
        df_final_salvar = pd.concat([df_historico_limpo, df_ocorrencias_novas], ignore_index=True)
        
        # Envia para o Google Sheets
        conn.update(data=df_final_salvar)
        st.success(f"✅ Ocorrências do dia {data_formatada} atualizadas com sucesso no Sheets!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
