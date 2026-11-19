"""FastAPI application factory and server configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

app = FastAPI(
    title="Automated Resume Screening API",
    description="Intelligent candidate resume parsing, skill matching, multi-factor scoring, and ranking engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Specific local origins for Next.js development (avoiding wildcard origins with credentials)
LOCAL_DASHBOARD_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Enable CORS for Next.js Recruiter Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_DASHBOARD_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    """Root endpoint with service metadata."""
    return {
        "service": "Automated Resume Screening Tool",
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/health",
        "sample_jobs": "/api/jobs"
    }
