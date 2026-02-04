import streamlit as st
import requests
import os
import time

# Helpers for Standalone Mode (Direct Backend Import)
import sys

# Configuration
# Default to localhost if env var not set. 
# In Streamlit Cloud, this won't be reachable, so we will fallback to Standalone.
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Restaurant Recommender",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        margin-top: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍽️ AI Restaurant Recommender")

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
    st.markdown("""
    **Status:** 🟢 Running in **Standalone Mode** (Serverless).
    """)
    # Initialize DB (only runs once thanks to cache_resource)
    try:
        init_standalone_backend()
    except Exception as e:
        st.error(f"Failed to initialize standalone backend: {e}")
        st.stop()
else:
    st.markdown(f"""
    **Status:** 🟢 Connected to Backend API at `{API_URL}`.
    """)

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

# Sidebar for controls
st.sidebar.header("🔍 Preferences")

cities_list = get_cities_wrapper()

if not cities_list:
    if USE_STANDALONE:
        st.error("No cities found in database. Please check logs.")
    else:
        st.warning(f"Connected to backend, but no cities found at {API_URL}.")
    # Don't stop entirely, let user see UI
    selected_city = "No Cities Available"
else:
    selected_city = st.sidebar.selectbox("📍 Select City", cities_list)

price_map = {"Cheap ($)": "$", "Moderate ($$)": "$$", "Expensive ($$$)": "$$$"}
selected_price_label = st.sidebar.selectbox("💰 Price Range", list(price_map.keys()), index=1)
price_category = price_map[selected_price_label]

limit = st.sidebar.slider("🔢 Number of Results", min_value=3, max_value=10, value=3)

if st.sidebar.button("✨ Get Recommendations", type="primary"):
    if not selected_city or selected_city == "No Cities Available":
        st.error("Please select a valid city.")
    else:
        with st.spinner("🤖 Asking the AI for the best spots..."):
            start_time = time.time()
            try:
                response = get_recommendations_wrapper(selected_city, price_category, limit)
                
                if response.status_code == 200:
                    data = response.json()
                    recs = data.get("recommendations", [])
                    
                    if recs:
                        st.canvas = st.empty()
                        st.success(f"Found {len(recs)} recommendations in {time.time() - start_time:.2f}s!")
                        
                        for i, rec in enumerate(recs, 1):
                            with st.container():
                                st.markdown(f"### #{rec.get('rank', i)} {rec.get('name')}")
                                
                                col1, col2, col3 = st.columns([1, 2, 1])
                                
                                with col1:
                                    st.metric("Rating", f"{rec.get('rating', 'N/A')} ⭐")
                                    st.caption(f"Cost: ₹{rec.get('cost_for_two', 'N/A')}")
                                    
                                with col2:
                                    st.markdown(f"**Location:** {rec.get('location')}")
                                    st.info(f"💡 {rec.get('reason')}")
                                    
                                with col3:
                                    if rec.get('has_online_delivery') or rec.get('online_order'):
                                        st.success("✅ Delivery")
                                    else:
                                        st.warning("❌ Dine-in Only")
                                        
                                st.divider()
                    else:
                        st.warning("No recommendations found. Try adjusting criteria.")
                else:
                    detail = "Error"
                    try:
                        detail = response.json().get("detail", response.text)
                    except:
                        pass
                    st.error(f"Error: {detail}")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"Mode: **{'Standalone' if USE_STANDALONE else 'API'}**")
