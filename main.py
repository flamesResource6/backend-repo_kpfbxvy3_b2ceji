import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Service, Inquiry, User, Product

app = FastAPI(title="IT Services API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "IT Services Backend is running"}

# ------------------------------------------------------
# Public Endpoints for Frontend
# ------------------------------------------------------

@app.get("/api/services", response_model=List[Service])
def list_services():
    try:
        docs = get_documents("service", {}, 100)
        # Convert Mongo docs to Service models (strip _id)
        services = []
        for d in docs:
            d.pop("_id", None)
            services.append(Service(**d))
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inquiries")
def create_inquiry(inquiry: Inquiry):
    try:
        _id = create_document("inquiry", inquiry)
        return {"status": "ok", "id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------
# Utility/Test
# ------------------------------------------------------

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    # Env flags
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ------------------------------------------------------
# Seed endpoint to pre-populate some services (idempotent)
# ------------------------------------------------------

class SeedResult(BaseModel):
    inserted: int

@app.post("/admin/seed", response_model=SeedResult)
def seed_services():
    """Create a few default services if collection is empty"""
    try:
        existing = get_documents("service")
        if existing:
            return SeedResult(inserted=0)
        defaults = [
            Service(
                title="Pembuatan Website",
                description="Website modern, cepat, dan mobile-friendly untuk bisnis Anda.",
                category="Development",
                features=["Landing page elegan", "CMS mudah digunakan", "SEO dasar"],
                starting_price=5000000,
                icon="globe"
            ),
            Service(
                title="Aplikasi Mobile",
                description="Aplikasi Android/iOS untuk skala startup hingga enterprise.",
                category="Development",
                features=["React Native/Flutter", "Integrasi API", "Deployment ke store"],
                starting_price=15000000,
                icon="smartphone"
            ),
            Service(
                title="Cloud & DevOps",
                description="Set up server, CI/CD, monitoring, hingga auto scaling.",
                category="Cloud",
                features=["Docker & Kubernetes", "AWS/GCP/Azure", "Observability"],
                starting_price=7000000,
                icon="cloud"
            ),
            Service(
                title="Konsultasi Keamanan",
                description="Audit keamanan, pentest, dan rekomendasi best practice.",
                category="Security",
                features=["Vulnerability assessment", "Pentest aplikasi", "Security hardening"],
                starting_price=6000000,
                icon="shield"
            )
        ]
        inserted = 0
        for s in defaults:
            create_document("service", s)
            inserted += 1
        return SeedResult(inserted=inserted)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
