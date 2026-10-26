# Aplikasi RAG Chatbot Metadata Masjid Syuhada Yogyakarta (Fixed)

Aplikasi web berbasis **Streamlit** dan **Retrieval-Augmented Generation (RAG)** untuk mempublikasikan metadata cagar budaya Masjid Syuhada Yogyakarta menggunakan standar **Dublin Core Metadata Initiative (DCMI)**.

## 📁 Struktur Project
- `app.py`: Kode utama aplikasi Streamlit dan logika RAG (ChromaDB + Gemini).
- `requirements.txt`: Daftar dependensi Python.
- `README.md`: Panduan instalasi dan deployment.
- `data/Dublin_Core_Metadata_Masjid_Syuhada.xlsx`: Dataset metadata Dublin Core.

## 🚀 Cara Menjalankan Secara Lokal
1. Ekstrak zip ini.
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

## ☁️ Cara Deploy ke Streamlit Cloud (streamlit.io)
1. Push project ini ke repositori **GitHub**.
2. Hubungkan akun GitHub di [share.streamlit.io](https://share.streamlit.io/).
3. Buat aplikasi baru dan arahkan ke file `app.py`.
4. Masukkan `GEMINI_API_KEY` pada menu **Advanced Settings -> Secrets**:
   ```toml
   GEMINI_API_KEY = "API_KEY_GEMINI_ANDA"
   ```
