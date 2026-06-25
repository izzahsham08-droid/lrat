# LRAT — Deployment Guide (Render)

This guide turns your local project into a public link your supervisor can open.
The whole tool runs as **one service**: FastAPI serves both the calculations and the website.

---

## How it works

1. You build the React frontend on your laptop (`npm run build`).
2. The build is copied into `backend/static/`.
3. FastAPI serves that built website AND the calculation API from one server.
4. Render runs that FastAPI server and gives you a public link.

---

## ONE-TIME SETUP

### Step 1 — Build the frontend locally

In your project folder (`Desktop\lrat`), double-click **`prepare_deploy.bat`**
(or run it in a terminal). This will:
- build the React app
- copy it into `backend\static\`

Wait until it says "Done!". You should now have a `backend\static\` folder
containing `index.html` and an `assets` folder.

### Step 2 — Put the project on GitHub

In a terminal inside `Desktop\lrat`:

```
git init
git add .
git commit -m "LRAT initial deploy"
```

Then create a new empty repository on github.com (no README), and run the
commands GitHub shows you, which look like:

```
git remote add origin https://github.com/YOUR_USERNAME/lrat.git
git branch -M main
git push -u origin main
```

### Step 3 — Deploy on Render

1. Go to https://render.com and sign in (you can sign in with GitHub).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub and select your **lrat** repository.
4. Render reads `render.yaml` automatically. Confirm these settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Choose the **Free** plan.
6. Click **Create Web Service**.

Render will build and deploy (takes 5-10 min the first time). When done, you get
a link like `https://lrat.onrender.com`.

---

## UPDATING THE TOOL LATER

Whenever you change the code:

1. Run **`prepare_deploy.bat`** again (rebuilds the frontend).
2. Push the changes:
   ```
   git add .
   git commit -m "describe your change"
   git push
   ```
3. Render automatically rebuilds and redeploys.

---

## NOTES

- **First load may be slow.** On the free plan, the server "sleeps" after ~15 min
  of inactivity. The first visit after sleeping takes ~30-50 seconds to wake up,
  then it's fast. Tell your supervisor to wait a moment on first load.
- **Each visitor gets their own blank form.** Auto-save is per-browser, so no one
  sees anyone else's data.
- **The link is private-ish.** Only people you give the link to will find it; it
  is not listed publicly. (It is not password-protected, though — tell me if you
  want that added.)
