#building a rag pipeline each time user asks query this flow will be followed

from langchain.prompts import ChatPromptTemplate

from langchain.schema.runnable import Runnable
from langdetect import detect
from langchain.schema import Document
import os
from dotenv import load_dotenv
load_dotenv()
gemini_api_key = os.getenv("GOOGLE_API_KEY")




try:
    from langchain_google_genai import ChatGoogleGenerativeAI as GeminiLLM
    print("[INFO] Using ChatGoogleGenerativeAI")
except ImportError:
    from langchain_google_genai import GoogleGenerativeAI as GeminiLLM
    print("[INFO] Using GoogleGenerativeAI")

from rag_pipeline.prompts import get_system_prompt

SECTION_HISTORIES = {
    "remedies": [],
    "schemes": [],
    "emergency": []
}


def detect_script_language(text):
    try:
        lang = detect(text)
        if lang == 'hi':
            if any('\u0900' <= c <= '\u097F' for c in text):
                return "Hindi-Devanagari"
            else:
                return "Hinglish"
        elif lang == 'en':
            return "English"
        else:
            if re.fullmatch(r'[a-zA-Z0-9\s\.,!?\'\"-]+', text):
                return "English"
    except:
        return "English"


def build_rag_chain(vector_db, context_type="all"):
    retriever=vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    if gemini_api_key:
        print("[DEBUG] Gemini API Key loaded successfully.")
        llm = GeminiLLM(model="gemini-2.0-flash", temperature=0.4, google_api_key=gemini_api_key)
    else:
        print("[WARNING] GOOGLE_API_KEY not found in .env! Falling back to ADC credentials.")
        llm = GeminiLLM(model="gemini-2.0-flash", temperature=0.4)



    def format_docs(docs):
       return "\n\n".join([doc.page_content for doc in docs])

    def rag_chain_fn(inputs):
       question = inputs["question"]
       section = inputs.get("section", "remedies")
       history = inputs.get("chat_history", [])[-5:]
       detected_lang = detect_script_language(question)

       system_prompt = get_system_prompt(context_type)
       system_prompt += "\nUse the previous conversation only if it is there ,and relevant context to answer clearly. If user asks for general recipes, check the previous health concern only if present in the conversation and provide recipes relevant to that."

       system_prompt += f"\n\nRespond in the same script/language as the user input, which is: {detected_lang}."
       print(f"[DEBUG] Section: {section}")
       print(f"[DEBUG] Detected language: {detected_lang}")
       print(f"[DEBUG] System prompt: {system_prompt}")

        # Combine chat messages history
       history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])

       print("[DEBUG] Last 5 messages in chat history:")
       for i, msg in enumerate(history, 1):
            print(f"  {i}. {msg['role'].capitalize()}: {msg['content']}")
        # Retrieve relevant documents
       docs = retriever.invoke(question)
       context = format_docs(docs)

        # Final formatted input to LLM
       full_input = f"{history_text}\n\nContext:\n{context}\n\nQuestion: {question}"
       prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{full_input}")
        ])

       final_prompt = prompt.invoke({"full_input": full_input})
       response = llm.invoke(final_prompt)

       SECTION_HISTORIES[section].append({"role": "user", "content": question})
       SECTION_HISTORIES[section].append({"role": "assistant", "content": response.content})

       return response

    return rag_chain_fn