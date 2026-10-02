import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.generators.solution_exporter import solution_exporter
from app.llm.contracts import NotebookPlan

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.post("/generate")
async def generate_notebook(plan: NotebookPlan):
    """Generate a notebook and return a downloadable ZIP bundle."""
    try:
        zip_bytes, validation_report = solution_exporter.build_bundle(plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notebook generation failed: {e}")

    if not validation_report.is_valid:
        # Return issues as a 422 with details rather than a broken ZIP
        issues = [i.model_dump() for i in validation_report.issues]
        raise HTTPException(
            status_code=422,
            detail={"message": "Generated notebook failed validation", "issues": issues},
        )

    filename = f"{plan.competition_title.lower().replace(' ', '_')}_notebook.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
