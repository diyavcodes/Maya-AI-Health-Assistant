# Maya: AI-Powered Health & Welfare Assistant

**Maya** is an interactive AI-powered chatbot and health assistant web application built with **Streamlit**, **LangChain**, and **Gemini LLM**. It helps users access **health remedies, government schemes, emergency resources, nearby hospitals, and real-time health alerts** in an intuitive and conversational interface.

---

## Features

### 1. Remedies
- Provides **Ayurvedic and home remedies** for common ailments.
- Uses **RAG (Retrieval-Augmented Generation)** to answer queries accurately based on PDF and JSON documents.
- Allows conversational queries with AI summarization.

### 2. Government Schemes
- Access detailed health-related government schemes.
- AI-based question-answering from official documents to provide instant information.

### 3. Emergency Guidance
- Provides instructions and guidelines from official manuals for urgent situations.
- Quickly answers emergency-related queries using AI.

### 4. Nearby Services
- Finds **hospitals, clinics, and healthcare facilities** near a given PIN code.
- Uses **OpenStreetMap & Overpass API** with Haversine distance calculation.
- Displays locations on an interactive **Folium map**.

### 5. Alerts
- Fetches **real-time weekly health alerts** from **IDSP (Integrated Disease Surveillance Program)** reports.
- Automatically extracts **state-wise disease outbreak data** from PDF reports.
- Generates concise, **news-style summaries** using Gemini LLM.
- Summaries focus on **accurate disease info**, avoiding hallucinations.

---

## Technology Stack

- **Frontend & UI**: Streamlit  
- **Backend AI**: LangChain + Gemini LLM   
- **Document Processing**: `pdfplumber` for PDFs, JSON for schemes  
- **Web Scraping**: `requests` + BeautifulSoup  
- **Mapping**: Folium + OpenStreetMap Overpass API  
- **Data Storage**: Session state in Streamlit  

---

