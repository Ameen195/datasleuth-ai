from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.agent.investigation import investigate_dataset

app = FastAPI(
    title="DataSleuth AI API",
    description="API for automated data quality investigation.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB per CSV


@app.get("/")
def root():
    return {
        "application": "DataSleuth AI",
        "message": "Data investigation API is running.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "datasleuth-ai-api",
    }


async def save_csv_upload(upload: UploadFile, destination: str) -> None:
    filename = upload.filename or ""

    if Path(filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail=f"{filename or 'Uploaded file'} must be a CSV file.",
        )

    size = 0

    with open(destination, "wb") as output:
        while True:
            chunk = await upload.read(1024 * 1024)

            if not chunk:
                break

            size += len(chunk)

            if size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="Each CSV file must be 20 MB or smaller.",
                )

            output.write(chunk)

    if size == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV files cannot be empty.",
        )


@app.post("/api/v1/investigations")
async def create_investigation(
    baseline: UploadFile = File(...),
    current: UploadFile = File(...),
):
    temporary_paths = []

    try:
        for _ in range(2):
            handle = tempfile.NamedTemporaryFile(
                suffix=".csv",
                delete=False,
            )
            temporary_paths.append(handle.name)
            handle.close()

        baseline_path, current_path = temporary_paths

        await save_csv_upload(baseline, baseline_path)
        await save_csv_upload(current, current_path)

        result = await run_in_threadpool(
            investigate_dataset,
            baseline_path,
            current_path,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        # Keep detailed errors in server logs, not in public API responses.
        print(f"Investigation failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Investigation failed. Check the backend logs.",
        ) from exc

    finally:
        for path in temporary_paths:
            try:
                os.remove(path)
            except OSError:
                pass

        await baseline.close()
        await current.close()
