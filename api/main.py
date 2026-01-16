"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import schools, history

app = FastAPI(
    title="Indonesia EdTech Lead Gen API",
    description="API for lead enrichment system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schools.router)
app.include_router(history.router)


@app.get("/")
async def root():
    return {"message": "Indonesia EdTech Lead Gen API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

