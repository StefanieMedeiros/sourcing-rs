import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime

st.set_page_config(page_title="Registro de Sourcing R&S", layout="centered")

st.markdown("""
    <style>
    .header-card {
        background-color: #0d0926;
        color: white;
        padding: 28px;
        border-radius: 16px;
        margin-bottom: 25px;
    }
    .badge {
        background-color: #2b1354;
        color: #d1b3ff;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
    <div class="header-card">
        <span class="badge">⚡ Registro de Sourcing R&S</span>
        <h2 style='color: white; margin-top: 10px; margin-bottom: 8px;'>Mapeamento e Indicadores de Vagas</h2>
        <p style='color: #b0a8c9; font-size: 14px;'>
            Preencha abaixo as informações.
        </p>
    </div>
""", unsafe_allow_html=True)

st.subheader("1. DADOS DA VAGA")
col1, col2 = st.columns(2)
with col1:
    assistente = st.text_input("Nome do Assistente", placeholder="Ex: Sabrina Silva")
    mes = st.selectbox("Mês de Referência", [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ])
    rp = st.text_input("Número da RP", placeholder="Ex: 9748")

with col2:
    empresa = st.text_input("Empresa / Cliente", placeholder="Ex: Illumina")
    cargo = st.text_input("Cargo", placeholder="Ex: Especialista de Cuidado ao Cliente")
    n_vagas = st.number_input("Número de Vagas", min_value=1, value=1, step=1)

tipo_vaga = st.selectbox(
    "Tipo de Vaga",
    ["TECH", "Operacionais & Adm", "DEI&P", "Projeto", "Executivo / Liderança"]
)

st.write("---")
st.subheader("2. MÉTRICAS E FUNIL DE CANDIDATOS")

col3, col4 = st.columns(2)
with col3:
    retornos_efetivos = st.number_input("N° Candidatos - Retornos Efetivos", min_value=0, value=0)
    agendados = st.number_input("N° Candidatos Agendados", min_value=0, value=0)
    entrevistados = st.number_input("N° Candidatos Entrevistados", min_value=0, value=0)

with col4:
    aprovados_shortlist = st.number_input("N° Aprovados / Shortlist Enviado", min_value=0, value=0)
    contratacoes = st.number_input("N° Contratações Realizadas", min_value=0, value=0)
    reprovacao_consultor = st.number_input("N° Reprovações do Consultor", min_value=0, value=0)

observacoes = st.text_area("Observações / Desafios do Hunting (Opcional):")

if st.button("Salvar Informações", type="primary", use_container_width=True):
    if not assistente or not empresa or not cargo:
        st.warning("Por favor, preencha os campos obrigatórios.")
    else:
        with st.spinner("Processando..."):
            feedback_ia = ""
            try:
                if "GEMINI_API_KEY" in st.secrets:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    Analise os dados do hunting:
                    - Vaga: {cargo} na empresa {empresa} ({tipo_vaga})
                    - Retornos: {retornos_efetivos} | Agendados: {agendados} | Entrevistados: {entrevistados} | Shortlist: {aprovados_shortlist} | Reprovações: {reprovacao_consultor}
                    - Observações: {observacoes}

                    Forneça um diagnóstico direto de 2 frases sobre a eficiência da busca.
                    """
                    response = model.generate_content(prompt)
                    feedback_ia = response.text
            except Exception as e:
                feedback_ia = f"Análise indisponível: {e}"

            if feedback_ia:
                st.info(f"💡 **Insight da IA sobre esta busca:**\n\n{feedback_ia}")

            # Envio dos dados para a Planilha via Web App URL
            payload = {
                "Data_Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Assistente": assistente,
                "Mês": mes,
                "RP": rp,
                "Empresa": empresa,
                "Cargo": cargo,
                "N_Vagas": n_vagas,
                "Tipo_Vaga": tipo_vaga,
                "Retornos_Efetivos": retornos_efetivos,
                "Agendados": agendados,
                "Entrevistados": entrevistados,
                "Aprovados_Shortlist": aprovados_shortlist,
                "Contratações": contratacoes,
                "Reprovações_Consultor": reprovacao_consultor,
                "Insight_IA": feedback_ia
            }

            try:
                web_app_url = st.secrets["WEB_APP_URL"]
                res = requests.post(web_app_url, json=payload)
                if res.status_code == 200:
                    st.success("Informações salvas com sucesso!")
                else:
                    st.error(f"Erro ao salvar: {res.status_code}")
            except Exception as e:
                st.error(f"Erro ao conectar com obanco de dados: {e}")
