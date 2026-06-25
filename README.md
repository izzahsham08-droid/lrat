# LRAT — Lightning Risk Assessment Tool
## React + FastAPI Version

---

## 📁 Project Structure

```
lrat/
├── backend/          ← FastAPI Python backend
│   ├── main.py       ← API routes
│   ├── pdf_generator.py
│   ├── requirements.txt
│   ├── engines/      ← Your original calculation engines
│   ├── modules/      ← N, P, L, Annex E modules
│   ├── models/       ← BuildingInput, Line, Zone
│   ├── mappings/     ← IEC lookup tables
│   ├── services/     ← building_builder.py
│   └── utils/
└── frontend/         ← React + Tailwind frontend
    ├── src/
    │   ├── pages/    ← Home, Building, Lines, Zones, Results
    │   ├── components/
    │   └── context/  ← Global state (AssessmentContext)
    └── package.json
```

---

## 🚀 Setup (One Time)

### 1. Install Python dependencies (backend)

```bash
cd lrat/backend
pip install -r requirements.txt
```

### 2. Install Node dependencies (frontend)

```bash
cd lrat/frontend
npm install
```

---

## ▶️ Running Locally

You need **two terminals** open at the same time.

### Terminal 1 — Backend

```bash
cd lrat/backend
uvicorn main:app --reload --port 8000
```

Backend will be at: http://localhost:8000

### Terminal 2 — Frontend

```bash
cd lrat/frontend
npm run dev
```

Frontend will be at: http://localhost:5173

Open http://localhost:5173 in your browser.

---

## 🌐 Deployment (Share with Link)

### Option A — Free (Recommended for FYP)

1. **Backend → Railway**
   - Go to https://railway.app
   - Create account → New Project → Deploy from GitHub
   - Push your `lrat/backend` folder to a GitHub repo
   - Railway auto-detects Python and deploys
   - Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - You get a URL like: `https://lrat-backend.railway.app`

2. **Frontend → Vercel**
   - Go to https://vercel.com
   - New Project → Import your GitHub repo (lrat/frontend folder)
   - Set environment variable: `VITE_API_URL=https://lrat-backend.railway.app`
   - Change fetch URLs in frontend from `/api/` to `${import.meta.env.VITE_API_URL}/`
   - You get a URL like: `https://lrat.vercel.app`

Share the Vercel URL with your supervisor — no login needed.

---

## 🔧 Quick Fix if CORS Error Appears

In `backend/main.py`, the CORS is already set to allow all origins (`"*"`),
so this should not be an issue.

---

## 📝 Notes

- All calculation engines are UNTOUCHED from your original Streamlit version
- The frontend uses React Router for clean page navigation with scroll-to-top
- Zone and Line forms fully reset when adding new entries
- Zones and Lines are re-editable via the pencil icon
- Results page combines Calculate + Results into one clean page
