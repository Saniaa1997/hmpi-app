# backend/utils.py
import json
import pandas as pd
import numpy as np

def load_limits(path="limits.json"):
    with open(path, "r") as f:
        return json.load(f)

def validate_dataframe(df: pd.DataFrame, required_metal_columns):
    """
    Returns (valid, report_dict).
    - checks numeric columns, missing coords, duplicates, units heuristics
    """
    report = {"missing_columns": [], "non_numeric": [], "missing_coords": 0, "rows": len(df)}
    for col in required_metal_columns:
        if col not in df.columns:
            report["missing_columns"].append(col)
        else:
            # check numeric
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    report["non_numeric"].append(col)
                except Exception:
                    report["non_numeric"].append(col)
    if "latitude" in df.columns and "longitude" in df.columns:
        report["missing_coords"] = int(df["latitude"].isna().sum() + df["longitude"].isna().sum())
    # quick unit heuristic: check magnitudes (if many values > 1000 maybe units are µg/L vs mg/L)
    magnitude = {}
    for col in required_metal_columns:
        if col in df.columns:
            s = df[col].dropna()
            if not s.empty:
                magnitude[col] = float(s.abs().median())
            else:
                magnitude[col] = np.nan
    report["median_magnitude"] = magnitude
    valid = len(report["missing_columns"]) == 0
    return valid, report

def categorize_hmpi(hmpi_value):
    # Tunable categories (example)
    if pd.isna(hmpi_value):
        return "Unknown"
    if hmpi_value < 50:
        return "Safe"
    if 50 <= hmpi_value < 100:
        return "Low Pollution"
    if 100 <= hmpi_value < 200:
        return "High Pollution"
    return "Very High Pollution"

def categorize_mci(mci_value):
    if pd.isna(mci_value):
        return "Unknown"
    if mci_value < 1:
        return "Safe"
    if 1 <= mci_value < 2:
        return "Alert"
    if 2 <= mci_value < 6:
        return "Moderately Affected"
    return "Seriously Affected"
