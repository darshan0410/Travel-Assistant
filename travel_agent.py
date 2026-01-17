import streamlit as st
import json
import os
from serpapi import GoogleSearch
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ------------------ LOAD ENV ------------------
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not SERPAPI_KEY or not OPENROUTER_API_KEY:
    st.error("❌ API keys missing in .env file")
    st.stop()

# OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ------------------ AI FUNCTION ------------------
def run_ai(prompt):
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": "You are a professional AI travel planner."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")

st.markdown("""
<style>
.title { text-align:center; font-size:36px; font-weight:bold; color:#ff5733; }
.subtitle { text-align:center; font-size:20px; color:#555; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip using AI</p>', unsafe_allow_html=True)

# ------------------ USER INPUTS ------------------
source = st.text_input("🛫 Departure City (IATA Code)", "BOM")
destination = st.text_input("🛬 Destination City (IATA Code)", "DEL")
num_days = st.slider("🕒 Trip Duration (Days)", 1, 14, 5)

travel_theme = st.selectbox(
    "🎭 Travel Theme",
    ["Couple Getaway", "Family Vacation", "Adventure Trip", "Solo Exploration"]
)

activity_preferences = st.text_area(
    "🌍 Preferred Activities",
    "Relaxing, sightseeing, local food"
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# ------------------ SIDEBAR ------------------
st.sidebar.title("🧳 Preferences")

budget = st.sidebar.radio("💰 Budget", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("🏨 Hotel Rating", ["Any", "3⭐", "4⭐", "5⭐"])

visa_required = st.sidebar.checkbox("🛂 Visa Required")
travel_insurance = st.sidebar.checkbox("🛡️ Travel Insurance")

# ------------------ FLIGHTS ------------------
def fetch_flights():
    params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": str(departure_date),
        "return_date": str(return_date),
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    return search.get_dict()

def extract_cheapest_flights(data):
    flights = data.get("best_flights", [])
    return sorted(flights, key=lambda x: x.get("price", float("inf")))[:3]

def format_datetime(t):
    try:
        return datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%d %b %Y | %I:%M %p")
    except:
        return "N/A"
    
def build_google_flights_link(source, destination, departure_date, return_date):
    return (
        "https://www.google.com/travel/flights?"
        f"q=Flights%20from%20{source}%20to%20{destination}"
        f"%20on%20{departure_date}%20returning%20{return_date}"
    )


# ------------------ GENERATE PLAN ------------------
if st.button("🚀 Generate Travel Plan"):
    with st.spinner("✈️ Fetching flights..."):
        flight_data = fetch_flights()
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("🔍 Researching destination..."):
        research = run_ai(
            f"Research top attractions, safety tips, and best experiences in {destination} "
            f"for a {num_days}-day {travel_theme}. Activities: {activity_preferences}."
        )

    with st.spinner("🏨 Finding hotels & food..."):
        hotels = run_ai(
            f"Suggest best hotels ({hotel_rating}) and restaurants in {destination} "
            f"for a {budget} budget."
        )

    with st.spinner("🗺️ Creating itinerary..."):
        itinerary = run_ai(
            f"Create a detailed {num_days}-day itinerary for {destination}. "
            f"Theme: {travel_theme}. Budget: {budget}. "
            f"Activities: {activity_preferences}. "
            f"Flights: {json.dumps(cheapest_flights)}."
        )

    # ------------------ DISPLAY ------------------
    st.subheader("✈️ Cheapest Flights")

    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
    
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                flights_info = flight.get("flights", [])
                if not flights_info:
                    st.warning("Flight details unavailable")
                    continue
    
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})
    
                airline = flights_info[0].get("airline", "Unknown Airline")
                price = flight.get("price", "N/A")
                duration = flight.get("total_duration", "N/A")
    
                dep_time = format_datetime(departure.get("time", ""))
                arr_time = format_datetime(arrival.get("time", ""))
    
                booking_link = build_google_flights_link(
                    source, destination, departure_date, return_date
                )
    
                st.markdown(
                    f"""
                    <div style="
                        border:1px solid #ddd;
                        border-radius:10px;
                        padding:15px;
                        background:#f9f9f9;
                        text-align:center;
                    ">
                        <h4>✈️ {airline}</h4>
                        <p><b>Departure:</b> {dep_time}</p>
                        <p><b>Arrival:</b> {arr_time}</p>
                        <p><b>Duration:</b> {duration} mins</p>
                        <h3 style="color:green;">₹ {price}</h3>
                        <a href="{booking_link}" target="_blank"
                           style="
                           display:inline-block;
                           padding:8px 16px;
                           background:#007bff;
                           color:white;
                           border-radius:6px;
                           text-decoration:none;">
                           🔗 View on Google Flights
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("⚠️ No flights found")
    

    st.subheader("🏨 Hotels & Restaurants")
    st.write(hotels)

    st.subheader("🗺️ Personalized Itinerary")
    st.write(itinerary)

    st.success("✅ Travel plan generated successfully!")
