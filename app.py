import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da página do Dashboard
st.set_page_config(page_title="Controle de Aprendizes", layout="wide")
st.title("📊 Painel de Controle de Faltas - Aprendizes")

# 1. Conexão com o Google Sheets
# Nota: Você precisará configurar as credenciais do Google Sheets no Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

# Carrega os dados atuais da planilha
try:
    df = conn.read(ttl=0)  # ttl=0 garante que sempre pegue o dado mais recente
except Exception as e:
    st.error("Erro ao conectar à planilha. Certifique-se de configurar as credenciais secretas do Streamlit.")
    # Dados de exemplo caso a planilha ainda não esteja conectada
    df = pd.DataFrame({
        "ID": range(1, 29),
        "Nome do Aprendiz": [f"Aprendiz {i}" for i in range(1, 29)],
        "Empresa": ["Ceratti", "Perfetti Van Melle", "Saint-Gobain", "Avery Dennison", "Duoflex"] * 5 + ["Ceratti"] * 3,
        "Status": ["Presente"] * 28,
        "Horário de Chegada": ["-"] * 28,
        "Possui Atestado": ["Não"] * 28,
        "Link do Atestado": [""] * 28
    })

# 2. Seção de Resumo/Métricas rápidas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Aprendizes", len(df))
with col2:
    total_faltas = len(df[df["Status"] == "Falta"])
    st.metric("Faltas Hoje", total_faltas)
with col3:
    total_atrasos = len(df[df["Status"] == "Atraso"])
    st.metric("Atrasos Hoje", total_atrasos)
with col4:
    total_atestados = len(df[df["Possui Atestado"] == "Sim"])
    st.metric("Atestados Entregues", total_atestados)

st.markdown("---")
st.subheader("📝 Tabela de Frequência Diária")
st.info("Dica: Você pode dar dois cliques em qualquer célula abaixo para editar os nomes, horários ou colar o link do atestado armazenado no seu Drive.")

# Listas para validação e seleção rápida nas colunas da tabela
lista_empresas = ["Ceratti", "Perfetti Van Melle", "Saint-Gobain", "Avery Dennison", "Duoflex"]
lista_status = ["Presente", "Atraso", "Falta"]
lista_atestado = ["Não", "Sim", "Não se aplica"]

# 3. Componente de Edição de Dados em Tempo Real
df_editado = st.data_editor(
    df,
    hide_index=True,
    num_rows="dynamic", # Permite adicionar ou remover aprendizes se necessário
    column_config={
        "ID": st.column_config.NumberColumn("ID", disabled=True),
        "Nome do Aprendiz": st.column_config.TextColumn("Nome do Aprendiz", required=True),
        "Empresa": st.column_config.SelectboxColumn("Empresa", options=lista_empresas, required=True),
        "Status": st.column_config.SelectboxColumn("Status", options=lista_status, required=True),
        "Horário de Chegada": st.column_config.TextColumn("Horário de Chegada (HH:MM)", help="Ex: 08:15. Use '-' se chegou no horário."),
        "Possui Atestado": st.column_config.SelectboxColumn("Possui Atestado?", options=lista_atestado),
        "Link do Atestado": st.column_config.LinkColumn("Link do Atestado (Drive/Dropbox)", help="Cole aqui o link do arquivo do atestado anexado na nuvem.")
    },
    use_container_width=True
)

# 4. Botão para Salvar as alterações de volta na Planilha do Google
st.markdown("")
if st.button("💾 Salvar Alterações Permanentemente", type="primary"):
    try:
        # Atualiza a planilha do Google com os novos dados editados na tela
        conn.update(data=df_editado)
        st.success("✅ Todas as alterações foram salvas com sucesso no Google Sheets!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}. Certifique-se de que a planilha permite escrita.")
