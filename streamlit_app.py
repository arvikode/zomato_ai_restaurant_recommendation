import streamlit as st
import requests
import os
import time

# Helpers for Standalone Mode (Direct Backend Import)
import sys

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Restaurant Guide",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
STYLING = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #13131f;
  --bg-card: rgba(30, 30, 40, 0.6);
  --bg-card-hover: rgba(40, 40, 50, 0.8);
  --text-primary: #ffffff;
  --text-secondary: #a1a1aa;
  --accent-primary: #6366f1;
  --accent-secondary: #ec4899;
  --accent-gradient: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
  --success: #10b981;
  --error: #ef4444;
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

/* Base Overrides */
.stApp {
    background-color: var(--bg-primary);
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 25%),
        radial-gradient(circle at 85% 30%, rgba(236, 72, 153, 0.15) 0%, transparent 25%);
    background-attachment: fixed;
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
}

/* Gradient Heading */
.heading-gradient {
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 0.5rem;
}

.subheading {
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 2rem;
    font-size: 1.1rem;
}

/* Input Containers */
.stSelectbox, .stSlider {
    background: transparent;
}

div[data-baseweb="select"] > div {
    background-color: rgba(30, 30, 40, 0.6) !important;
    border: 1px solid var(--glass-border) !important;
    color: white !important;
    border-radius: 8px !important;
}

div[data-testid="stMarkdownContainer"] p {
    color: var(--text-secondary);
}

/* Buttons */
div.stButton > button {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: transform 0.2s !important;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

div.stButton > button:active {
    color: white !important;
}

div.stButton > button:focus {
    color: white !important;
    box-shadow: none !important;
}

/* Custom Cards (HTML) */
.restaurant-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--glass-shadow);
    transition: transform 0.2s;
    height: 100%;
}

.restaurant-card:hover {
    transform: translateY(-4px);
    background: var(--bg-card-hover);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
}

.rank-badge {
    background: var(--accent-gradient);
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white;
    margin-right: 12px;
    flex-shrink: 0;
}

.card-title {
    color: var(--text-primary);
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
}

.card-meta {
    font-size: 0.9rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.25rem;
}

.rating-badge {
    color: var(--success);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
}

.price-tag {
    color: var(--text-primary);
    font-weight: 600;
}

.reason-box {
    background: rgba(99, 102, 241, 0.1);
    border-left: 3px solid var(--accent-primary);
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin-top: 1rem;
    font-style: italic;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* Streamlit Overrides to Hide Default Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(STYLING, unsafe_allow_html=True)

# --- INITIALIZATION & MODE CHECK ---

@st.cache_resource
def check_api_server(url):
    """Check if the external API server is running."""
    try:
        response = requests.get(f"{url}/", timeout=1)
        return response.status_code == 200
    except Exception:
        return False

@st.cache_resource
def init_standalone_backend():
    """Initialize the database for standalone mode."""
    # Lazy import to allow UI to load even if imports fail (though they shouldn't)
    from backend.ingest import is_db_empty, run_ingest
    
    if is_db_empty():
        with st.spinner("Initializing Database (Downloading dataset)... this may take a minute"):
            run_ingest()
    return True

# Determine Mode
is_api_live = check_api_server(API_URL)
USE_STANDALONE = not is_api_live

if USE_STANDALONE:
    # Initialize DB (only runs once thanks to cache_resource)
    try:
        init_standalone_backend()
    except Exception as e:
        st.error(f"Failed to initialize standalone backend: {e}")
        st.stop()


# --- LOGIC WRAPPERS ---

def get_cities_wrapper():
    if not USE_STANDALONE:
        try:
            response = requests.get(f"{API_URL}/cities", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass # Fallback? No, if API mode was detected, we stay in it.
        return []
    else:
        # Standalone Logic
        from backend.routers import cities
        from backend.database import get_db
        # Get a fresh session
        db_gen = get_db()
        db = next(db_gen)
        try:
            return cities.list_cities(db=db)
        except Exception as e:
            st.error(f"DB Error: {e}")
            return []
        finally:
            db.close()

def get_recommendations_wrapper(city, price_category, limit):
    if not USE_STANDALONE:
        payload = {
            "city": city,
            "price_category": price_category,
            "limit": limit
        }
        response = requests.post(f"{API_URL}/recommendations", json=payload, timeout=60)
        return response
    else:
        # Standalone Logic
        from backend.routers import recommendations
        from backend.schemas import RecommendationRequest
        from backend.database import get_db
        from fastapi import HTTPException
        
        db_gen = get_db()
        db = next(db_gen)
        
        req = RecommendationRequest(
            city=city,
            price_category=price_category,
            limit=limit
        )
        
        # Mocking a response object to keep interface consistent
        class MockResponse:
            def __init__(self, data, status_code=200):
                self._data = data
                self.status_code = status_code
                self.text = ""
                
            def json(self):
                return self._data
        
        try:
            # We call the router function directly
            # Note: The router function might raise HTTPException, we need to catch it
            data = recommendations.get_recommendations(body=req, db=db)
            # data is a RecommendationResponse (Pydantic model)
            # We need to convert it to dict for consistency with API response
            return MockResponse(data.model_dump())
        except HTTPException as he:
            return MockResponse({"detail": he.detail}, status_code=he.status_code)
        except Exception as e:
            return MockResponse({"detail": str(e)}, status_code=500)
        finally:
            db.close()


# --- APP INTERFACE ---

# Header
st.markdown('<div class="heading-gradient">AI Restaurant Guide</div>', unsafe_allow_html=True)
st.markdown('<div class="subheading">Discover the perfect dining spot with AI-powered recommendations tailored to your taste and budget.</div>', unsafe_allow_html=True)

# Helper for layout
def space(n):
    for _ in range(n):
        st.write("")

# Search Container
with st.container():
    # We use columns to center the search box somewhat, or just full width
    col_input1, col_input2, col_input3 = st.columns([1, 1, 1])
    
    cities_list = get_cities_wrapper()
    if not cities_list:
        cities_list = ["No Cities Available"]
        
    with col_input1:
        st.markdown("**Select City**")
        selected_city = st.selectbox("Select City", cities_list, label_visibility="collapsed")
        
    with col_input2:
        st.markdown("**Price Range**")
        price_map = {"Cheap ($)": "$", "Moderate ($$)": "$$", "Expensive ($$$)": "$$$"}
        selected_price_label = st.selectbox("Price Range", list(price_map.keys()), index=1, label_visibility="collapsed")
        price_category = price_map[selected_price_label]
        
    with col_input3:
        st.markdown("**Recommendations**")
        limit = st.slider("Number of Results", min_value=3, max_value=12, value=3,  label_visibility="collapsed")

    space(1)
    
    if st.button("✨ Get Recommendations"):
        if not selected_city or selected_city == "No Cities Available":
            st.error("Please select a valid city.")
        else:
            with st.spinner("🤖 Asking the AI for the best spots..."):
                response = get_recommendations_wrapper(selected_city, price_category, limit)
                
                if response.status_code == 200:
                    data = response.json()
                    recs = data.get("recommendations", [])
                    
                    if recs:
                        st.markdown(f"### Found {len(recs)} Top Picks")
                        
                        # Grid Layout for Cards
                        # We will render rows of 3 columns
                        
                        cols = st.columns(3)
                        for i, rec in enumerate(recs):
                            col = cols[i % 3]
                            with col:
                                delivery_icon = "✅" if (rec.get('has_online_delivery') or rec.get('online_order')) else "❌"
                                delivery_text = "Online Delivery Available" if (rec.get('has_online_delivery') or rec.get('online_order')) else "No Online Delivery"
                                # CSS class can't be used easily inside standard widgets, but we use HTML card
                                
                                html_card = f"""
                                <div class="restaurant-card">
                                    <div class="card-header">
                                        <div style="display:flex; align-items:center;">
                                            <div class="rank-badge">{rec.get('rank', i+1)}</div>
                                            <div>
                                                <h3 class="card-title">{rec.get('name')}</h3>
                                                <div class="card-meta">📍 {rec.get('location')}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div style="display:flex; justify-content:space-between; margin-top:10px;">
                                        <div class="rating-badge">★ {rec.get('rating', 'N/A')} / 5</div>
                                        <div class="price-tag">₹{rec.get('cost_for_two', 'N/A')} for two</div>
                                    </div>
                                    <div class="card-meta" style="margin-top:8px; font-size:0.85rem;">
                                        {delivery_icon} {delivery_text}
                                    </div>
                                    <div class="reason-box">
                                        "{rec.get('reason')}"
                                    </div>
                                </div>
                                """
                                st.markdown(html_card, unsafe_allow_html=True)
                    else:
                        st.warning("No recommendations found. Try adjusting criteria.")
                else:
                    st.error(f"Error: {response.text}")

# Debug / Footer info (small)
st.markdown("---")
mode_label = "Standalone Mode" if USE_STANDALONE else "API Mode"
st.caption(f"Running in {mode_label} | Built with Streamlit & FastAPI")
