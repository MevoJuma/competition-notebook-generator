import math
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import polars as pl

from app.schemas.profile import ColumnProfile, DatasetProfileCreate

logger = logging.getLogger("app.analyzers.data_profiler")

class DataProfiler:
    """High-performance data profiler using Polars."""

    @classmethod
    def profile_file(
        cls, 
        file_path: Path, 
        competition_id: str, 
        file_id: Optional[str] = None, 
        role: str = "unknown",
        sample_size: int = 5
    ) -> DatasetProfileCreate:
        """Profile a CSV or Parquet file using Polars."""
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        dataset_name = file_path.name
        
        if file_path.suffix.lower() == ".csv":
            df = pl.read_csv(file_path, try_parse_dates=True, ignore_errors=True)
        elif file_path.suffix.lower() in [".parquet", ".pq"]:
            df = pl.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format for profiling: {file_path.suffix}")

        row_count = df.height
        column_count = df.width
        memory_bytes = df.estimated_size()

        schema_definition = {name: str(dtype) for name, dtype in df.schema.items()}
        
        column_profiles = {}
        for col_name in df.columns:
            series = df[col_name]
            dtype = str(series.dtype)
            null_count = series.null_count()
            
            unique_count = None
            min_value = None
            max_value = None
            mean_value = None
            
            if series.dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64):
                if null_count < row_count:
                    min_val = series.min()
                    max_val = series.max()
                    mean_val = series.mean()
                    
                    min_value = float(min_val) if min_val is not None else None
                    max_value = float(max_val) if max_val is not None else None
                    mean_value = float(mean_val) if mean_val is not None else None
                    
                    if min_value is not None and (math.isnan(min_value) or math.isinf(min_value)):
                        min_value = None
                    if max_value is not None and (math.isnan(max_value) or math.isinf(max_value)):
                        max_value = None
                    if mean_value is not None and (math.isnan(mean_value) or math.isinf(mean_value)):
                        mean_value = None

            unique_count = series.n_unique()

            column_profiles[col_name] = ColumnProfile(
                name=col_name,
                dtype=dtype,
                null_count=null_count,
                unique_count=unique_count,
                min_value=min_value,
                max_value=max_value,
                mean_value=mean_value
            )

        sample_df = df.head(sample_size)
        sample_rows_raw = sample_df.to_dicts()
        sample_rows = []
        for row in sample_rows_raw:
            cleaned_row = {}
            for k, v in row.items():
                if v is None:
                    cleaned_row[k] = None
                elif isinstance(v, (int, float, str, bool)):
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        cleaned_row[k] = None
                    else:
                        cleaned_row[k] = v
                else:
                    cleaned_row[k] = str(v)
            sample_rows.append(cleaned_row)
            
        return DatasetProfileCreate(
            competition_id=competition_id,
            file_id=file_id,
            dataset_name=dataset_name,
            role=role,
            row_count=row_count,
            column_count=column_count,
            memory_bytes=memory_bytes,
            schema_definition=schema_definition,
            column_profiles=column_profiles,
            sample_rows=sample_rows
        )

data_profiler = DataProfiler()
