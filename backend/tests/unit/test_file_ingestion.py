import io
import zipfile
import pytest
from httpx import AsyncClient

from app.analyzers.file_detector import get_file_type, infer_file_category_from_name, is_supported_file
from app.models.enums import FileCategory


def test_file_type_detection():
    """Verify supported and unsupported file extensions."""
    assert get_file_type("data.csv") == "csv"
    assert get_file_type("train.parquet") == "parquet"
    assert get_file_type("dataset.pq") == "parquet"
    assert get_file_type("rules.pdf") == "pdf"
    assert get_file_type("description.docx") == "docx"
    assert get_file_type("archive.zip") == "zip"
    assert get_file_type("script.py") == "unknown"
    assert is_supported_file("data.csv") is True
    assert is_supported_file("malicious.exe") is False


def test_file_category_heuristics():
    """Verify initial category assignments based on filename heuristics."""
    assert infer_file_category_from_name("Train.csv") == FileCategory.TRAIN_DATA
    assert infer_file_category_from_name("train_v2.parquet") == FileCategory.TRAIN_DATA
    assert infer_file_category_from_name("Test.csv") == FileCategory.TEST_DATA
    assert infer_file_category_from_name("SampleSubmission.csv") == FileCategory.SAMPLE_SUBMISSION
    assert infer_file_category_from_name("sample_sub.csv") == FileCategory.SAMPLE_SUBMISSION
    assert infer_file_category_from_name("variable_definitions.csv") == FileCategory.METADATA_DICTIONARY
    assert infer_file_category_from_name("competition_rules.pdf") == FileCategory.DOCUMENTATION_RULES


@pytest.mark.asyncio
async def test_competition_and_file_upload_api_flow(async_client: AsyncClient):
    """Integration test: Create competition, upload single files & zip archive, verify categorization, and delete."""
    # 1. Create Competition
    comp_payload = {
        "title": "Zindi Road Safety Challenge",
        "platform": "zindi",
        "description": "Predict traffic collision hotspots in Nairobi.",
    }
    create_res = await async_client.post("/api/v1/competitions", json=comp_payload)
    assert create_res.status_code == 201
    comp = create_res.json()
    comp_id = comp["id"]
    assert comp["slug"] == "zindi-road-safety-challenge"
    assert comp["status"] == "UPLOADED"

    # 2. Upload individual CSV file
    csv_content = b"id,location,collision_occurred\n1,ZoneA,1\n2,ZoneB,0\n"
    files = [
        ("files", ("Train.csv", csv_content, "text/csv")),
    ]
    upload_res = await async_client.post(f"/api/v1/competitions/{comp_id}/files", files=files)
    assert upload_res.status_code == 201
    uploaded_files = upload_res.json()
    assert len(uploaded_files) == 1
    assert uploaded_files[0]["category"] == FileCategory.TRAIN_DATA.value
    assert uploaded_files[0]["file_type"] == "csv"

    # 3. Upload a ZIP archive containing Test.csv and sample_submission.csv
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Test.csv", "id,location\n3,ZoneC\n4,ZoneD\n")
        zf.writestr("sample_submission.csv", "id,collision_occurred\n3,0.5\n4,0.5\n")
    zip_buffer.seek(0)

    zip_files = [
        ("files", ("competition_data.zip", zip_buffer.getvalue(), "application/zip")),
    ]
    zip_res = await async_client.post(f"/api/v1/competitions/{comp_id}/files", files=zip_files)
    assert zip_res.status_code == 201
    extracted_records = zip_res.json()
    # Should contain the zip itself + the 2 extracted files
    assert len(extracted_records) == 3

    # 4. List all files for competition
    list_res = await async_client.get(f"/api/v1/competitions/{comp_id}/files")
    assert list_res.status_code == 200
    all_files = list_res.json()
    assert len(all_files) == 4  # Train.csv + zip + Test.csv + sample_submission.csv

    categories = {f["filename"]: f["category"] for f in all_files}
    assert categories["Train.csv"] == FileCategory.TRAIN_DATA.value
    assert categories["Test.csv"] == FileCategory.TEST_DATA.value
    assert categories["sample_submission.csv"] == FileCategory.SAMPLE_SUBMISSION.value

    # 5. Fetch competition detail (eager-loaded files)
    detail_res = await async_client.get(f"/api/v1/competitions/{comp_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["files"]) == 4

    # 6. Delete competition
    del_res = await async_client.delete(f"/api/v1/competitions/{comp_id}")
    assert del_res.status_code == 204

    # Verify 404 after deletion
    get_res = await async_client.get(f"/api/v1/competitions/{comp_id}")
    assert get_res.status_code == 404
