from pathlib import Path
import pytest
from app.analyzers.data_profiler import data_profiler

def test_data_profiler_csv(tmp_path: Path):
    csv_file = tmp_path / "train.csv"
    csv_file.write_text(
        "id,age,salary,city,is_active\n"
        "1,25,50000.5,New York,true\n"
        "2,30,,London,false\n"
        "3,,75000.0,Paris,\n"
        "4,22,45000.0,New York,true\n"
    )

    profile = data_profiler.profile_file(
        file_path=csv_file,
        competition_id="comp-123",
        role="train"
    )

    assert profile.dataset_name == "train.csv"
    assert profile.row_count == 4
    assert profile.column_count == 5
    
    assert "age" in profile.column_profiles
    age_prof = profile.column_profiles["age"]
    assert age_prof.null_count == 1
    assert age_prof.min_value == 22.0
    assert age_prof.max_value == 30.0
    
    assert "city" in profile.column_profiles
    city_prof = profile.column_profiles["city"]
    assert city_prof.null_count == 0
    assert city_prof.unique_count == 3
    
    assert len(profile.sample_rows) == 4
    assert profile.sample_rows[0]["city"] == "New York"
