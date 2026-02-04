# Server Setup & Usage Guide

## Quick Start

### 1. Start the Backend Server
Run this command from the project root. It uses the virtual environment directly, so no activation is needed.

```powershell
.venv\Scripts\uvicorn backend.main:app --reload
```

- **URL:** [http://localhost:8000](http://localhost:8000)
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Run the Terminal Test
Open a **new terminal window** (keep the server running) and run:

```powershell
.venv\Scripts\python scripts/terminal_test.py
```

Follow the interactive prompts to select a city and price range.

---

## Configuration (`.env`)

If you encounter AI errors, check your `.env` file configuration.

### GEMINI (Google AI) - Recommended
We use `gemini-flash-latest` or `gemini-2.0-flash` for the free tier.

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-flash-latest
```

### Common Errors

**429 Resource Exhausted / Quota Exceeded**
- **Cause:** You hit the rate limit for the free tier model.
- **Fix:** Switch `GEMINI_MODEL` in `.env` to one of the following:
  - `gemini-flash-latest` (Best generic alias)
  - `gemini-2.0-flash-lite-001` (Lightweight)
  - `gemini-1.5-flash`

**UnicodeEncodeError (Rupee symbol)**
- **Cause:** Windows PowerShell sometimes defaults to limited character sets (cp1252).
- **Fix:** This is just a display error in the test script. The server is working effectively. You can run `chcp 65001` in PowerShell before running the script to fix the display.
