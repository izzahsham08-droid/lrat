from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Optional
import tempfile, os, traceback

from services.building_builder import build_building_from_session
from engines.risk_engine import RiskEngine
from engines.frequency_engine import FrequencyEngine
from engines.annex_e_risk_engine import AnnexERiskEngine
from engines.protection_recommendation_engine import ProtectionRecommendationEngine

app = FastAPI(title="LRAT API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssessmentRequest(BaseModel):
    building_data: dict
    lines_data: list
    zones_data: list


class PDFRequest(BaseModel):
    building_data: dict
    lines_data: list
    zones_data: list
    risk_results: dict
    frequency_results: dict
    annex_e_results: dict
    protection_recommendations: dict
    frequency_recommendations: dict


# ---------------------------------------------------------------------------
# API endpoints (all under /api so they don't clash with the React app)
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "LRAT API running"}


@app.post("/api/calculate")
def calculate(req: AssessmentRequest):
    try:
        building = build_building_from_session(
            req.building_data,
            req.lines_data,
            req.zones_data
        )
        risk_results = RiskEngine.calculate_R(building)
        protection_recommendations = ProtectionRecommendationEngine.generate(building, risk_results)
        frequency_results = FrequencyEngine.calculate_F(building)
        frequency_recommendations = ProtectionRecommendationEngine.generate_frequency(building, frequency_results)
        annex_e_results = AnnexERiskEngine.calculate_RE(building)

        # ---- SPD consolidation across risk and frequency ----
        # If frequency needs a higher SPD than risk (or vice versa), the
        # stronger requirement governs both assessments. Flag this so the
        # user knows one SPD level satisfies both.
        SPD_ORDER = ["none", "III_IV", "II", "I", "better_2_5", "better_3_75", "better_5"]

        def spd_idx(key):
            try: return SPD_ORDER.index(key)
            except ValueError: return 0

        def get_rec_spd(recs_for_zone, field):
            """Find the SPD key recommended for a given field in a zone's recs."""
            for rec in (recs_for_zone or []):
                for action in rec.get("actions", []):
                    if action.get("field") == field:
                        return action.get("value")
            return None

        for zone_name in set(list(protection_recommendations.keys()) + list(frequency_recommendations.keys())):
            for field in ["power_spd_level", "telecom_spd_level"]:
                risk_key = get_rec_spd(protection_recommendations.get(zone_name, []), field)
                freq_key = get_rec_spd(frequency_recommendations.get(zone_name, []), field)

                if not risk_key and not freq_key:
                    continue

                risk_idx = spd_idx(risk_key) if risk_key else 0
                freq_idx = spd_idx(freq_key) if freq_key else 0

                if freq_idx > risk_idx:
                    # Frequency needs higher SPD — flag risk recommendations
                    for rec in protection_recommendations.get(zone_name, []):
                        for action in rec.get("actions", []):
                            if action.get("field") == field:
                                action["spd_governed_by"] = "frequency"
                                action["governing_note"] = (
                                    f"Frequency assessment requires a higher SPD level "
                                    f"({SPD_ORDER[freq_idx].replace('_', ' ')}). "
                                    f"Apply the frequency recommendation to satisfy both."
                                )
                elif risk_idx > freq_idx:
                    # Risk needs higher SPD — flag frequency recommendations
                    for rec in frequency_recommendations.get(zone_name, []):
                        for action in rec.get("actions", []):
                            if action.get("field") == field:
                                action["spd_governed_by"] = "risk"
                                action["governing_note"] = (
                                    f"Risk assessment requires a higher SPD level "
                                    f"({SPD_ORDER[risk_idx].replace('_', ' ')}). "
                                    f"Applying the risk recommendation also satisfies frequency."
                                )

        return {
            "risk_results": risk_results,
            "protection_recommendations": protection_recommendations,
            "frequency_results": frequency_results,
            "frequency_recommendations": frequency_recommendations,
            "annex_e_results": annex_e_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.post("/api/generate-pdf")
def generate_pdf(req: PDFRequest):
    try:
        from pdf_generator import generate_pdf_report
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        generate_pdf_report(
            tmp.name,
            req.building_data, req.lines_data, req.zones_data,
            req.risk_results, req.frequency_results, req.annex_e_results,
            req.protection_recommendations, req.frequency_recommendations
        )
        return FileResponse(tmp.name, media_type="application/pdf", filename="lightning_risk_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Serve the built React app (single-service deployment)
# ---------------------------------------------------------------------------
# The React build is copied to ./static during deployment (see build script).
# If it exists, mount it; otherwise the API still works on its own.

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(STATIC_DIR):
    # Serve built assets (JS/CSS/images)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    # Catch-all: any non-API route returns index.html so React Router works
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        # If the requested file exists in static, serve it; else index.html
        candidate = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"status": "LRAT API running (no static build found)"}
