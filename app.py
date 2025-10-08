import streamlit as st
from modules.document_loader import load_files
from modules.vector_store import get_vector_db
from rag_pipeline.rag_pipeline import build_rag_chain
import requests
from bs4 import BeautifulSoup
import pdfplumber
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import os
from dotenv import load_dotenv
import datetime

# ---------------- Load Environment ---------------- #
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI as GeminiLLM
except ImportError:
    from langchain_google_genai import GoogleGenerativeAI as GeminiLLM

llm = GeminiLLM(model="gemini-2.0-flash", temperature=0.4, google_api_key=api_key)

# ---------------- Page Setup ---------------- #
st.set_page_config(page_title="Maya Chatbot", layout="wide")
st.title("Maya: Your Health & Welfare Assistant")

# ---------------- Sidebar Section ---------------- #
section = st.sidebar.radio("Select Section", ["Remedies", "Schemes", "Emergency", "Nearby Services", "Alerts"])
context_type_map = {"Remedies": "remedies", "Schemes": "schemes", "Emergency": "emergency"}
context_type = context_type_map.get(section, "")

# ---------------- Section-Specific Files ---------------- #
file_paths = []
if section == "Remedies":
    file_paths = [
        "documents/remedies/8.1.4-Details-of-Promotional-measures-undertaken-for-each-activity.pdf",
        "documents/remedies/Ayurvedic-Home-Remedies-English.pdf",
        "documents/remedies/Food_Recipes_From_AYUSH.pdf"
    ]
elif section == "Schemes":
    file_paths = [
        "documents/schemes/6851513623Nutrition-support-DBT-Scheme-details.pdf",
        "documents/schemes/97827133331523438951.pdf",
        "documents/schemes/Ayushman Bharat Scheme.pdf",
        "documents/schemes/general_schemes.json"
    ]
elif section == "Emergency":
    file_paths = ["documents/FA-manual-1.pdf"]

# ---------------- RAG Chat Sections ---------------- #
if section in ["Remedies", "Schemes", "Emergency"]:
    # Load or reuse vector DB
    if f"vector_db_{section}" not in st.session_state:
        with st.spinner(f"Loading documents for {section}..."):
            documents = load_files(file_paths)
            vector_db = get_vector_db(documents=documents)
            st.session_state[f"vector_db_{section}"] = vector_db
    else:
        vector_db = st.session_state[f"vector_db_{section}"]

    # Build or reuse RAG chain
    if f"rag_chain_{section}" not in st.session_state:
        st.session_state[f"rag_chain_{section}"] = build_rag_chain(vector_db, context_type=context_type)

    rag_chain = st.session_state[f"rag_chain_{section}"]

    # Chat history
    chat_history_key = f"chat_history_{section}"
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []

    # Input key
    input_key = f"user_input_{section}"
    if input_key not in st.session_state:
        st.session_state[input_key] = ""

    # Display chat
    st.subheader("Conversation with Maya")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state[chat_history_key]:
            if msg["role"] == "user":
                st.markdown(f"""
                    <div style='display:flex; justify-content:flex-start; margin:5px 0;'>
                        <div style='background-color:#F1F1F2; padding:10px; border-radius:10px; max-width:60%; text-align:left;'>{msg['content']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='display:flex; justify-content:flex-end; margin:5px 0;'>
                        <div style='background-color:#E9D8FD; padding:10px; border-radius:10px; max-width:60%; text-align:left;'>{msg['content']}</div>
                    </div>""", unsafe_allow_html=True)

    # ---------------- Chat Input Using Form ---------------- #
    def send_message():
        if st.session_state[input_key].strip():
            user_msg = st.session_state[input_key]
            st.session_state[chat_history_key].append({"role": "user", "content": user_msg})
            with st.spinner("Maya is thinking..."):
                result = rag_chain({
                    "question": user_msg,
                    "chat_history": st.session_state[chat_history_key]
                })
                bot_response = result.content if hasattr(result, "content") else result
                st.session_state[chat_history_key].append({"role": "assistant", "content": bot_response})
            st.session_state[input_key] = ""  # clear input

    st.text_input("💬 Ask your question:", key=input_key, on_change=send_message)



# ---------------- Nearby Services Section ---------------- #
if section == "Nearby Services":
    st.subheader("Find Nearby Hospitals and Clinics by PIN Code")
    pincode = st.text_input("Enter your PIN code:")
    find_clicked = st.button("Find Services")

    if find_clicked and pincode.strip():
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={pincode}, India&format=json"
            geo_res = requests.get(geo_url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                geo_res_json = geo_res.json()
            except Exception:
                geo_res_json = []

            if not geo_res_json:
                st.error("❌ Invalid PIN code or location not found.")
            else:
                lat, lon = float(geo_res_json[0]["lat"]), float(geo_res_json[0]["lon"])
                query = f"""
                    [out:json];
                    (node["amenity"~"hospital|clinic"](around:5000,{lat},{lon});
                     way["amenity"~"hospital|clinic"](around:5000,{lat},{lon});
                     relation["amenity"~"hospital|clinic"](around:5000,{lat},{lon});
                    );
                    out center;
                """
                overpass_url = "https://overpass-api.de/api/interpreter"
                response = requests.post(overpass_url, data=query, headers={"User-Agent": "Mozilla/5.0"})
                try:
                    data = response.json()
                except Exception:
                    st.error("Overpass API returned invalid response.")
                    data = {"elements": []}

                # Haversine function
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c

                hospitals = []
                for el in data.get("elements", []):
                    lat_h = el.get("lat") or el.get("center", {}).get("lat")
                    lon_h = el.get("lon") or el.get("center", {}).get("lon")
                    if lat_h and lon_h:
                        distance = haversine(lat, lon, float(lat_h), float(lon_h))
                        hospitals.append({
                            "name": el.get("tags", {}).get("name", "Unknown"),
                            "lat": float(lat_h),
                            "lon": float(lon_h),
                            "type": el.get("tags", {}).get("amenity", "N/A"),
                            "distance": distance
                        })

                hospitals = sorted(hospitals, key=lambda x: x["distance"])[:5]
                st.session_state["nearby_lat"] = lat
                st.session_state["nearby_lon"] = lon
                st.session_state["hospitals"] = hospitals

        except Exception as e:   # <-- FIX: close try block properly
            st.error(f"Error fetching services: {e}")

    # Display results if already in session state
    if "nearby_lat" in st.session_state and "hospitals" in st.session_state:
        lat, lon, hospitals = (
            st.session_state["nearby_lat"],
            st.session_state["nearby_lon"],
            st.session_state["hospitals"]
        )
        st.markdown("### 5 Nearest Hospitals & Clinics")
        for h in hospitals:
            st.write(f"**{h['name']}** ({h['type']}) - {h['distance']:.2f} km away")

        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)

        for h in hospitals:
            folium.Marker(
                [h["lat"], h["lon"]],
                popup=f"{h['name']} ({h['type']})\nDistance: {h['distance']:.2f} km",
                icon=folium.Icon(color="red", icon="plus")
            ).add_to(m)

        st_folium(m, width=700, height=500)


# ---------------- Alerts Section ---------------- #
if section == "Alerts":
    st.subheader("🛑 Real-Time Health Alerts (IDSP Weekly Reports)")
    all_states = [
        "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
        "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra",
        "Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu",
        "Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir",
        "Ladakh","Puducherry","Chandigarh"
    ]
    selected_states = st.sidebar.multiselect("Select states to track:", all_states)

    try:
        url = "https://idsp.mohfw.gov.in/index4.php?lang=1&level=0&linkid=406&lid=3689"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        pdf_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".pdf")]
        if not pdf_links:
            st.error("No reports found.")
        else:
            latest_pdf = pdf_links[0]
            if not latest_pdf.startswith("http"):
                latest_pdf = "https://idsp.mohfw.gov.in" + latest_pdf.replace("..","")

            # Cache PDF weekly
            week_number = datetime.date.today().isocalendar()[1]
            pdf_path = f"latest_report_week_{week_number}.pdf"
            if not os.path.exists(pdf_path):
                try:
                    pdf_res = requests.get(latest_pdf)
                    with open(pdf_path,"wb") as f:
                        f.write(pdf_res.content)
                except Exception as e:
                    st.error(f"Failed to download latest report: {e}")
                    pdf_path = None

            if pdf_path and os.path.exists(pdf_path):
                text = ""
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
                    text = ""

                for state in selected_states:
                    state_text = "\n".join([line for line in text.splitlines() if state in line])
                    if not state_text.strip():
                        st.warning(f"No {state}-specific alerts found.")
                    else:
                        st.markdown(f"### 📰 {state} Outbreak Headlines")
                        prompt = (
                            f"Summarize the following outbreak report into 3-5 short headlines in news style and also give short information about the headlines, no introductory line by you, just direct headlines, "
                            f"mention disease for {state}:\n\n{state_text}"
                        )
                        try:
                            summary = llm.invoke(prompt)
                            st.write(summary.content if hasattr(summary,'content') else summary)
                        except Exception as e:
                            st.error(f"Error generating summary for {state}: {e}")

    except Exception as e:
        st.error(f"Error fetching alerts: {e}")
