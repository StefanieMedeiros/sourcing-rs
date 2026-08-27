import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página e layout
st.set_page_config(page_title="Registro de Sourcing R&S", layout="centered")

# Visual estilo Card Escuro
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
            Preencha os dados do levantamento para alimentar os indicadores de eficiência, conversão e qualidade no BI.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- SEÇÃO 1: DADOS DA VAGA & ASSISTENTE ---
st.subheader("📌 1. DADOS DA VAGA")
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

# --- SEÇÃO 2: MÉTRICAS DE MAPPING / FUNIL DE CANDIDATOS ---
st.subheader("📊 2. MÉTRICAS E FUNIL DE CANDIDATOS")

col3, col4 = st.columns(2)
with col3:
    retornos_efetivos = st.number_input("N° Candidatos - Retornos Efetivos", min_value=0, value=0)
    agendados = st.number_input("N° Candidatos Agendados", min_value=0, value=0)
    entrevistados = st.number_input("N° Candidatos Entrevistados", min_value=0, value=0)

with col4:
    aprovados_shortlist = st.number_input("N° Aprovados / Shortlist Enviado", min_value=0, value=0)
    contratacoes = st.number_input("N° Contratações Realizadas", min_value=0, value=0)
    reprovacao_consultor = st.number_input("N° Reprovações do Consultor", min_value=0, value=0)

observacoes = st.text_area("Observações / Desafios do Hunting (Opcional):", placeholder="Ex: Perfil com escassez no mercado...")

# --- BOTÃO DE AÇÃO ---
if st.button("💾 Salvar Indicadores na Base do BI", type="primary", use_container_width=True):
    if not assistente or not empresa or not cargo:
        st.warning("Por favor, preencha os campos obrigatórios: Assistente, Empresa e Cargo.")
    else:
        with st.spinner("Analisando registros e atualizando base do BI..."):
            
            # IA Gemini gera uma análise automática da qualidade do hunting
            feedback_ia = ""
            if "GEMINI_API_KEY" in st.secrets:
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    Atue como um Analista Sênior de R&S. Analise os dados do hunting abaixo:
                    - Vaga: {cargo} na empresa {empresa} ({tipo_vaga})
                    - Retornos Efetivos: {retornos_efetivos}
                    - Agendados: {agendados} | Entrevistados: {entrevistados} | Shortlist: {aprovados_shortlist} | Reprovações: {reprovacao_consultor}
                    - Observações: {observacoes}

                    Forneça um diagnóstico de 2 a 3 frases destacando a eficiência da busca ou onde está o gargalo.
                    """
                    response = model.generate_content(prompt)
                    feedback_ia = response.text
                except Exception:
                    feedback_ia = "Sem análise automática no momento."

            if feedback_ia:
                st.info(f"💡 **Insight da IA sobre esta busca:**\n\n{feedback_ia}")

            # Gravação no Google Sheets
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_existente = conn.read()

                novo_registro = pd.DataFrame([{
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
                }])

                df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("✅ Indicadores gravados com sucesso na sua planilha do BI!")
            except Exception as e:
                st.error(f"Erro ao salvar na planilha: {e}")
