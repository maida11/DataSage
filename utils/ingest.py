import pandas as pd
import json
from utils.state import AgentState
import numpy as np
def convert_numpy(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    return str(obj)
def ingest_csv(csv_path: str) -> AgentState:

    df = pd.read_csv(csv_path)

    profile = {}
    for col in df.columns:
        col_data = df[col]
        col_profile = {
            "dtype": str(col_data.dtype),
            "null_count": int(col_data.isnull().sum()),
            "null_pct": round(col_data.isnull().mean() * 100, 1),
            "unique_count": int(col_data.nunique()),
        }

        if pd.api.types.is_numeric_dtype(col_data):
            col_profile.update({
                "mean": round(col_data.mean(), 2),
                "median": round(col_data.median(), 2),
                "std": round(col_data.std(), 2),
                "min": round(col_data.min(), 2),
                "max": round(col_data.max(), 2),
                "skewness": round(col_data.skew(), 2),
            })

        if pd.api.types.is_object_dtype(col_data):
            col_profile.update({
                "sample_values": col_data.dropna().unique()[:5].tolist(),
                "has_whitespace": bool(
                    col_data.str.contains(r'^\s|\s$', na=False).any()
                ),
                "has_mixed_case": bool(
                    col_data.nunique() != col_data.str.title().nunique()
                ),
            })

        profile[col] = col_profile

    print(f" Loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    return {
        "csv_path": csv_path,
        "column_names": df.columns.tolist(),
        "sample_rows": df.head(5).to_string(index=False),
        "data_profile": json.dumps(profile, indent=2, default=convert_numpy),
        "plan": "",
        "code": "",
        "error": None,
        "error_count": 0,
        "logs": ""
    }