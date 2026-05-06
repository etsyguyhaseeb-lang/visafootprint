from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Report

router = APIRouter()


@router.get("/report/{job_id}")
async def get_report(job_id: str, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.status != "done":
        raise HTTPException(status_code=202, detail=f"Report not ready yet. Status: {report.status}")
    return report.report_json


@router.get("/report/{job_id}/pdf")
async def download_pdf(job_id: str, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.status != "done":
        raise HTTPException(status_code=202, detail=f"Report not ready yet. Status: {report.status}")
    if not report.pdf_path or not Path(report.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"visa_screening_report_{job_id[:8]}.pdf",
    )
