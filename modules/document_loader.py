import os
import glob
import json
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
import fitz

def load_pdf(file_path):
    doc=fitz.open(file_path)
    text=""
    for page in doc:
        text+=page.get_text()
    metadata= {"source": os.path.basename(file_path)}
    print(f"[DEBUG] PDF loaded with {len(text)} characters.")
    return Document(page_content=text, metadata=metadata)

def load_json(file_path):
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []

    if isinstance(data, list):
        for i, entry in enumerate(data):
            
            content_lines = []
            for key, value in entry.items():
                
                pretty_key = key.replace('_', ' ').title()
                content_lines.append(f"**{pretty_key}:** {value}")

            content = "\n".join(content_lines)

            if "rajasthan" in content.lower():
                print(f"[DEBUG] 🔍 Entry {i} contains 'Rajasthan'.")

            documents.append(Document(
                page_content=content,
                metadata={"source": os.path.basename(file_path)}
            ))
            print(f"[INFO] Loaded {len(documents)} documents from JSON.")
    else:
        print(f"[ERROR] Expected a list of entries, got {type(data)}")

    return documents

def load_files(file_paths):
    
    documents = []

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"[Warning] File not found: {file_path}")
            continue

        if file_path.endswith('.pdf'):
            doc = load_pdf(file_path)
            print(f"[DEBUG] 📄 PDF doc preview: {doc.page_content[:200]}...\n")
            documents.append(doc)

        elif file_path.endswith('.json'):
            json_docs = load_json(file_path)
            for i, d in enumerate(json_docs[:2]):
                print(f"[DEBUG] 📝 JSON doc {i} preview: {d.page_content[:200]}...\n")
            documents.extend(json_docs)

        else:
            print(f"[WARNING] Unsupported file type: {file_path}")

    print(f"[INFO] ✅ Total documents loaded: {len(documents)}")

    return documents