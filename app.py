import os
import pandas as pd
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from google import genai

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="AI Chatbot Cagar Budaya - Masjid Syuhada",
    page_icon="🕌",
    layout="wide"
)

st.title("🕌 AI Chatbot Informasi Cagar Budaya Masjid Syuhada")
st.caption("Aplikasi Publikasi Metadata Arsitektur & Sejarah berbasis Dublin Core & RAG (Retrieval-Augmented Generation)")

# ==========================================
# 2. INISIALISASI API KEY & GEMINI CLIENT
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", None))

with st.sidebar:
    st.header("⚙️ Pengaturan & Status")
    if not api_key:
        api_key = st.text_input("Masukkan Google Gemini API Key:", type="password")
        st.info("💡 Dapatkan API Key gratis di [Google AI Studio](https://aistudio.google.com/).")
    
    st.markdown("---")
    st.markdown("### 📚 Data Referensi")
    st.markdown("Bot ini dilatih menggunakan standar metadata **Dublin Core (DCMI)** untuk arsitektur Masjid Syuhada Yogyakarta.")

if not api_key:
    st.warning("⚠️ Harap masukkan Google Gemini API Key di sidebar untuk memulai percakapan.")
    st.stop()

# Inisialisasi Google GenAI Client
client = genai.Client(api_key=api_key)

# ==========================================
# 3. SETUP VECTOR DATABASE (CHROMADB & RAG)
# ==========================================
@st.cache_resource(show_spinner="Memuat Vector Database Metadata...")
def init_vector_db():
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name="masjid_syuhada_dcmi",
        embedding_function=emb_fn
    )
    
    file_path = "data/Dublin_Core_Metadata_Masjid_Syuhada.xlsx"
    if not os.path.exists(file_path):
        file_path = "Dublin_Core_Metadata_Masjid_Syuhada.xlsx"
        
    df = pd.read_excel(file_path, sheet_name=0)
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        title_val = str(row.get('dc:title', ''))
        desc_val = str(row.get('dc:description', ''))
        chunk_val = str(row.get('chunk_text_rag', ''))
        
        full_text = "Judul: " + title_val + ". Deskripsi: " + desc_val + " Chunk: " + chunk_val
        
        documents.append(full_text)
        ids.append(str(row.get('dc:identifier', f"ID-{idx}")))
        
        metadata_item = {
            "title": title_val,
            "creator": str(row.get('dc:creator', '')),
            "subject": str(row.get('dc:subject', '')),
            "date": str(row.get('dc:date', '')),
            "type": str(row.get('dc:type', '')),
            "format": str(row.get('dc:format', '')),
            "coverage": str(row.get('dc:coverage', ''))
        }
        metadatas.append(metadata_item)
        
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    return collection, df

collection, df_metadata = init_vector_db()

with st.sidebar:
    with st.expander("📊 Lihat Data Metadata (Dublin Core)"):
        st.dataframe(df_metadata[['dc:identifier', 'dc:title', 'dc:subject']], use_container_width=True)

# ==========================================
# 4. CHAT HISTORY & RAG RETRIEVAL ENGINE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya asisten virtual Masjid Syuhada Yogyakarta. Silakan tanyakan hal seputar sejarah, arsitektur, atau simbolisme bangunan masjid."}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Tanyakan sesuatu tentang Masjid Syuhada... (contoh: Apa arti 17 anak tangga?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    results = collection.query(query_texts=[prompt], n_results=3)
    retrieved_docs = results['documents'][0]
    retrieved_metadatas = results['metadatas'][0]
    
    context_str = ""
    for i, (doc, meta) in enumerate(zip(retrieved_docs, retrieved_metadatas), start=1):
        context_str += "\n--- Dokumen " + str(i) + " ---\n"
        context_str += "Judul: " + str(meta.get('title')) + "\n"
        context_str += "Subjek/Topik: " + str(meta.get('subject')) + "\n"
        context_str += "Isi: " + str(doc) + "\n"

    system_instruction = (
        "Anda adalah Asisten Pakar Publikasi Cagar Budaya Masjid Syuhada Yogyakarta. "
        "Tugas Anda adalah menjawab pertanyaan pengunjung secara ramah, akurat, dan informatif "
        "berdasarkan konteks metadata Dublin Core yang diberikan.\n\n"
        "Aturan:\n"
        "1. Jawab pertanyaan HANYA berdasarkan konteks relevan yang diberikan di bawah.\n"
        "2. Jika informasi tidak ditemukan dalam konteks, katakan secara sopan bahwa data tersebut belum tersedia pada basis data metadata.\n"
        "3. Cantumkan simbolisme atau fakta sejarah jika relevan dengan pertanyaan."
    )
    
    user_prompt = (
        "KONTEKS METADATA MASJID SYUHADA:\n" + context_str + "\n\n"
        "PERTANYAAN PENGUNJUNG:\n" + prompt + "\n\n"
        "JAWABAN:"
    )
    
    with st.chat_message("assistant"):
        with st.spinner("Mencari metadata & menyusun jawaban..."):
            try:
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=user_prompt,
                    config={'system_instruction': system_instruction}
                )
                answer = response.text
                st.markdown(answer)
                
                with st.expander("🔍 Sumber Rujukan Context RAG (Dublin Core)"):
                    for meta in retrieved_metadatas:
                        st.write("- **" + str(meta.get('title')) + "** | *Subjek:* " + str(meta.get('subject')))
                        
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error("Gagal menghasilkan response: " + str(e))
