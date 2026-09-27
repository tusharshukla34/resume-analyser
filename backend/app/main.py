from fastapi import FastAPI

app = FastAPI(title="Resume Analyzer API")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "resume-analyzer-backend"}