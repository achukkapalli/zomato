# Phase 6 — Manual Testing Checklist

This checklist is designed to verify the end-to-end recommendation flow in the Streamlit application and the developer CLI tool.

## 1) Run Automated Tests (Sanity)

Run the full automated test suite using pytest to ensure all code builds and behaves correctly:

```bash
python -m pytest
```

Expected output:
- **97 passed** (with 3 skipped tests representing optional live integration checks).

---

## 2) Launch the Web UI (Streamlit)

Start the Streamlit application server:

```bash
streamlit run src/app/main.py
```

Verify:
- The UI initializes without syntax or rendering errors.
- The top caption displays the count of loaded restaurants (e.g. `51,717` restaurants loaded).

---

## 3) Demo Flow (Acceptance Criteria)

In the Streamlit interface:
1. Select a neighborhood in Bangalore under **City** (e.g. `Indiranagar` or `BTM`).
2. Select a **Budget** (e.g. `medium`).
3. Select a **Cuisine** (e.g. `Italian`).
4. Set a **Minimum Rating** (e.g. `4.0` using the slider).
5. Add **Additional Preferences** (e.g. `family-friendly, rooftop seating`).
6. Click **Get recommendations**.

Expected:
- The loading spinner appears during candidate extraction and LLM ranking.
- The UI displays the ranked recommendations inside styled cards showing the rank badge (`#1`), rating badge, estimated cost badge, cuisine badge, neighborhood address, and custom AI explanation.
- An overall summary paragraph is rendered above the picks.

---

## 4) Empty State Flow

Try querying for a city or neighborhood that does not exist in the dataset (e.g. `Tokyo` or a broad non-local name like `"Bangalore"`):
1. In the CLI:
   ```bash
   python -m src.cli --location Tokyo --budget medium
   ```
Expected:
- The return payload is a structured JSON representation of an `EmptyFilterResult`.
- It includes a `NO_LOCATION_MATCH` reason code, a user-facing error message, and a list of suggestions.

---

## 5) LLM Fallback & Graceful Failure

Verify that the system gracefully degrades to rating-based ranking when Groq is unavailable:
1. Unset your `GROQ_API_KEY` (or change it to an invalid value in your `.env` file).
2. Start the Streamlit application.
3. Submit your preferences (e.g. `Indiranagar`, `medium`, `Italian`).

Expected:
- The UI completes the recommendation pipeline without crashing.
- A prominent yellow warning banner appears at the top:  
  `⚠️ LLM Recommendation Service is currently unavailable or not configured. Displaying fallback recommendations ranked by rating.`
- The recommended cards display fallback explanations generated from templates.

---

## Note: Optional FastAPI Backend Route

If you chose to build the FastAPI API and frontend split (Option B in architecture), you can start the backend server via:
```bash
uvicorn src.api.main:app --reload --port 8000
```
This route is out of scope for the Streamlit monolith MVP release.
