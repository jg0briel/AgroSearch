from utils import normalize, stemmer, STOPWORDS
from collections import defaultdict
from pypdf import PdfReader
import streamlit as st
import math
import re

st.title("Motor de Busca Inteligente - AgroSearch")

st.subheader("Coleção de Documentos")

uploaded_files = st.file_uploader(
    "Envie os documentos (.txt, .pdf):", 
    type=["txt", "pdf"], 
    accept_multiple_files=True
)

stm = st.checkbox("Realizar Stemming?")
stpw = st.checkbox("Remover Stopwords?")

if "termos_docs" not in st.session_state:
    st.session_state["termos_docs"] = {}
if "indice_invertido" not in st.session_state:
    st.session_state["indice_invertido"] = {}

if st.button("Processar documentos"):
    docs = []
    if uploaded_files:
        for file in uploaded_files:
            texto_doc = ""
            
            if file.name.endswith(".txt"):
                texto_doc = file.read().decode("utf-8").strip()
            elif file.name.endswith(".pdf"):
                reader = PdfReader(file)
                
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        texto_doc += extracted + "\n"
                texto_doc = texto_doc.strip()

            if texto_doc:
                docs.append(texto_doc)
    
    termos_temp = {}
    for i, doc in enumerate(docs, 1):
        tokens = re.findall(r'\b\w+\b', doc)
        tokens = [normalize(t) for t in tokens]

        if stpw:
            tokens = [t for t in tokens if t not in STOPWORDS]

        if stm:
            tokens = [stemmer(t) for t in tokens]

        termos_temp[f'Doc{i}'] = tokens

    st.session_state["termos_docs"] = termos_temp
    
    i_invertido = defaultdict(list)
    for doc_id, lista_termos in termos_temp.items():
        for termo in lista_termos:
            if doc_id not in i_invertido[termo.lower()]:
                i_invertido[termo.lower()].append(doc_id)
                
    st.session_state["indice_invertido"] = dict(i_invertido)
    st.success(f"{len(docs)} documento(s) processado(s) com sucesso!")

if st.session_state["termos_docs"]:
    with st.expander("Documentos Processados (Índice Direto)"):
        st.json(st.session_state["termos_docs"])

    st.subheader("Índice Invertido")
    st.json(st.session_state["indice_invertido"])

query = st.text_input("Consulta do Termo (Query):")
if st.button("Calcular TF-IDF"):
    termos_docs = st.session_state["termos_docs"]
    
    if not termos_docs:
        st.warning("Processe os documentos primeiro.")
    else:
        N = len(termos_docs)
        
        idf = {}
        todos_termos = set()
        for doc_id, termos in termos_docs.items():
            todos_termos.update(termos)
            
        for termo in todos_termos:
            df = sum(1 for termos in termos_docs.values() if termo in termos)
            idf[termo] = math.log(N / df) if df > 0 else 0.0

        tfidf_resultados = {}
        
        for doc_id, termos in termos_docs.items():
            total_termos_doc = len(termos)
            tfidf_resultados[doc_id] = {}
            
            if total_termos_doc == 0:
                continue
                
            frequencias = {}
            for termo in termos:
                frequencias[termo] = frequencias.get(termo, 0) + 1
                
            for termo, freq in frequencias.items():
                tf = freq / total_termos_doc
                tfidf_resultados[doc_id][termo] = tf * idf[termo]

            if doc_id == f"Doc{N}":
                st.subheader("Resultados do TF-IDF por Documento")
                st.json(tfidf_resultados)
            
            if query.strip():
                query_tokens = re.findall(r'\b\w+\b', query)
                query_tokens = [normalize(t) for t in query_tokens]
                if stpw:
                    query_tokens = [t for t in query_tokens if t not in STOPWORDS]
                if stm:
                    query_tokens = [stemmer(t) for t in query_tokens]

                if doc_id == f"Doc{N}":
                    st.markdown(f"**Análise de relevância para a consulta:** `{query}`")
                
                pontuacoes = {}
                for d_id, scores in tfidf_resultados.items():
                    score_doc = sum(scores.get(t, 0.0) for t in query_tokens)
                    pontuacoes[d_id] = score_doc
                    
                docs_ordenados = sorted(pontuacoes.items(), key=lambda x: x[1], reverse=True)

                if doc_id == f"Doc{N}":
                    st.write("**Ranking de Relevância (Documentos):**")
                    for d_id, score in docs_ordenados:
                        st.write(f"- **{d_id}**: Pontuação TF-IDF = {score:.4f}")