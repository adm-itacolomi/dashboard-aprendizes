import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da página do Dashboard
st.set_page_config(page_title="Controle Mensal de Aprendizes", layout="wide")
st.title("📊 Painel de Controle de Faltas - Mensal por Empresa")

# 1. Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Criação de dados padrão de segurança (caso a conexão falhe)
df_padrao = pd.DataFrame({
    "Mês": ["Junho"] * 28,
    "Ano": [2026] * 28,
    "Nome do Aprendiz": [f"Aprendiz {i}" for i in range(1, 29)],
    "Empresa": ["Ceratti", "Perfetti Van Melle", "Saint-Gobain", "Avery Dennison", "Duoflex"] * 5 + ["Ceratti", "Perfetti Van Melle", "Saint-Gobain"],
    "Status": ["Presente"] * 28,
    "Horário de Chegada": ["-"] * 28,
    "Possui Atestado": ["Não"] * 28,
    "Link do Atestado": [""] * 28
})

# Tenta carregar os dados da planilha, se falhar usa os dados padrão
try:
    df = conn.read(ttl=0)
    # Se a planilha estiver vazia ou der erro de colunas, usa o padrão
    if df.empty or "Empresa" not in df.columns:
        df = df_padrao
except Exception as e:
    st.warning("Nota: Exibindo banco de dados local seguro. Verifique a conexão com o Google Sheets se as alterações não salvarem.")
    df = df_padrao

# 2. FILTROS DE TEMPO (Separação por Mês e Ano)
st.sidebar.header("📅 Selecione o Período do Relatório")

lista_anos = [2026, 2027, 2028]
lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

ano_selecionado = st.sidebar.selectbox("Ano", lista_anos)
mes_selecionado = st.sidebar.selectbox("Mês", lista_meses, index=5) # Padrão em Junho

# Filtrando o banco de dados
df_filtrado = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]

# Se o mês selecionado ainda não tiver dados na planilha, gera os 28 aprendizes para esse mês
if df_filtrado.empty:
    df_filtrado = df_padrao.copy()
    df_filtrado["Mês"] = mes_selecionado
    df_filtrado["Ano"] = ano_selecionado

# 3. ORDENAÇÃO POR EMPRESA
df_filtrado = df_filtrado.sort_values(by=["Empresa", "Nome do Aprendiz"]).reset_index(drop=True)

# 4. Seção de Resumo/Métricas rápidas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Aprendizes no Mês", len(df_filtrado))
with col2:
    total_faltas = len(df_filtrado[df_filtrado["Status"] == "Falta"])
    st.metric(f"Faltas em {mes_selecionado}", total_faltas)
with col3:
    total_atrasos = len(df_filtrado[df_filtrado["Status"] == "Atraso"])
    st.metric(f"Atrasos em {mes_selecionado}", total_atrasos)
with col4:
    total_atestados = len(df_filtrado[df_filtrado["Possui Atestado"] == "Sim"])
    st.metric("Atestados Retidos", total_atestados)

st.markdown("---")
st.subheader(f"📝 Tabela de Frequência - {mes_selecionado} de {ano_selecionado}")

# Listas para seleção nas colunas
lista_empresas = ["Ceratti", "Perfetti Van Melle", "Saint-Gobain", "Avery Dennison", "Duoflex"]
lista_status = ["Presente", "Atraso", "Falta"]
lista_atestado = ["Não", "Sim", "Não se aplica"]

# 5. Componente de Edição de Dados em Tempo Real
df_editado = st.data_editor(
    df_filtrado,
    hide_index=True,
    num_rows="dynamic", 
    column_config={
        "Mês": st.column_config.SelectboxColumn("Mês", options=lista_meses, required=True),
        "Ano": st.column_config.NumberColumn("Ano", format="%d", required=True),
        "Nome do Aprendiz": st.column_config.TextColumn("Nome do Aprendiz", required=True),
        "Empresa": st.column_config.SelectboxColumn("Empresa", options=lista_empresas, required=True),
        "Status": st.column_config.SelectboxColumn("Status", options=lista_status, required=True),
        "Horário de Chegada": st.column_config.TextColumn("Horário de Chegada (HH:MM)"),
        "Possui Atestado": st.column_config.SelectboxColumn("Possui Atestado?", options=lista_atestado),
        "Link do Atestado": st.column_config.LinkColumn("Link do Atestado")
    },
    use_container_width=True
)

# 6. Botão para Salvar as alterações
st.markdown("")
if st.button("💾 Salvar Alterações Permanentemente", type="primary"):
    try:
        # Junta o editado com o resto para não perder histórico
        df_nao_editado = df[~((df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado))]
        df_final_para_salvar = pd.concat([df_nao_editado, df_editado], ignore_index=True)
        
        conn.update(data=df_final_para_salvar)
        st.success(f"✅ Dados de {mes_selecionado} salvos com sucesso!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar diretamente na planilha: {e}. Verifique as permissões de Editor no Drive.")
