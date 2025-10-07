import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def get_vector_db(documents=None):
   

    persist_directory = "chroma_db"

    
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        raise EnvironmentError("Please set the HUGGINGFACEHUB_API_TOKEN environment variable.")

    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        try:
            return Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
        except:
            pass  

   
    if not documents:
        raise ValueError("No vector DB found and no documents provided to create one.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)

    db = Chroma.from_documents(
        split_docs,
        embeddings,
        persist_directory=persist_directory
    )
    db.persist()
    return db

