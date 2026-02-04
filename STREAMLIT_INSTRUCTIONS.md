
# Streamlit App Instructions

This project includes a Streamlit frontend for the Restaurant Recommendation System.
It is designed to run in two modes:

1.  **Standalone Mode (Default for Streamlit Cloud)**: The app runs entirely within Streamlit, managing its own database and logic. No separate backend server is needed.
2.  **API Mode (Development)**: The app connects to a separately running FastAPI backend (e.g., `uvicorn backend.main:app`).

## Deployment on Streamlit Community Cloud

This app is ready for one-click deployment!

1.  **Push your code to GitHub.**
2.  **Deploy on Streamlit Cloud:**
    *   Select `streamlit_app.py` as the main file.
3.  **Configure Secrets:**
    *   Go to App Settings -> Secrets.
    *   Add your API keys (Gemini or Grok) just like in `.env`:
        ```toml
        GEMINI_API_KEY = "your-key-here"
        # Or
        GROK_API_KEY = "your-key-here"
        ```
    *   (Optional) If you want to force API Mode, set `API_URL = "https://your-backend-url.com"`.

The app will automatically detect if an API server is running at `API_URL` (defaults to localhost:8000). If not, it switches to **Standalone Mode**, initializes the database (downloads from HuggingFace), and runs locally.

## Running Locally

### Option 1: Standalone (Easiest)

Just run Streamlit. It will handle the rest.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Option 2: With Separate Backend (For Dev)

Run the backend in one terminal:
```bash
uvicorn backend.main:app --reload
```

Run Streamlit in another:
```bash
streamlit run streamlit_app.py
```
The app will detect the running backend and connect to it.
