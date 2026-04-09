import uuid
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from main import run_pipeline
from database import create_db, save_job, get_all_jobs
from dotenv import load_dotenv
load_dotenv(override=False)
app = FastAPI(title="DataSage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_db()

@app.get("/")
def root():
    return {"status": "DataSage API is running"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    job_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(BASE_DIR, "data", f"upload_{job_id}.csv")

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Define outputs_dir BEFORE using it
    outputs_dir = os.path.join(BASE_DIR, "outputs")

    final_state = run_pipeline(save_path)

    print("FINAL STATE ERROR:", final_state.get("error"))
    print("FINAL STATE LOGS:", final_state.get("logs", "")[:200])

    outputs_dir = os.path.join(BASE_DIR, "outputs")
    saved_dir = os.path.join(BASE_DIR, "outputs", "saved")

    # If final run failed but we have saved charts from a successful attempt, use those
    if final_state.get("error") and os.path.exists(saved_dir) and len(os.listdir(saved_dir)) > 0:
        chart_source = saved_dir
        chart_prefix = "/outputs/saved"
    else:
        chart_source = outputs_dir
        chart_prefix = "/outputs"

    print("CHARTS FOUND:", os.listdir(chart_source))

    cleaned_csv = "/outputs/cleaned_dataset.csv" if os.path.exists(
        os.path.join(outputs_dir, "cleaned_dataset.csv")
    ) else None

    output_files = [
        f"{chart_prefix}/{f}"
        for f in os.listdir(chart_source)
        if f.endswith(".png")
    ]

    save_job(
        job_id=job_id,
        filename=file.filename,
        status="failed" if final_state.get("error") else "success",
        charts_count=len(output_files),
        logs=final_state.get("logs", "")
    )

    return {
        "job_id": job_id,
        "logs": final_state.get("agent_logs", ""),
        "error": final_state.get("error", None),
        "charts": output_files,
        "cleaned_csv": cleaned_csv
    }


@app.get("/jobs")
def list_jobs():
    jobs = get_all_jobs()
    return [
        {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "charts_count": job.charts_count,
            "created_at": job.created_at.isoformat()
        }
        for job in jobs
    ]


# Always mount static files LAST
app.mount("/outputs", StaticFiles(directory=os.path.join(BASE_DIR, "outputs")), name="outputs")