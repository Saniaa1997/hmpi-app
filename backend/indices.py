# backend/indices.py
import pandas as pd
import numpy as np

def _safe_get(row, col):
    val = row.get(col, None)
    if pd.isna(val):
        return None
    try:
        return float(val)
    except Exception:
        return None

def calculate_hmpi(df: pd.DataFrame, limits: dict, weight_scheme: str = "1/Si"):
    """
    Returns a pandas Series of HMPI values.
    Qi = (Ci / Si) * 100
    Wi = 1/Si (default) or equal
    HMPI = sum(Wi * Qi) / sum(Wi)
    """
    metals = list(limits.keys())
    hmpi_vals = []
    for _, row in df.iterrows():
        Qi_sum = 0.0
        Wi_sum = 0.0
        for m in metals:
            Ci = _safe_get(row, m)
            Si = limits[m]
            if Ci is None or Si is None or Si == 0:
                continue
            Qi = (Ci / Si) * 100.0
            Wi = (1.0 / Si) if weight_scheme == "1/Si" else 1.0
            Qi_sum += Qi * Wi
            Wi_sum += Wi
        hmpi_vals.append((Qi_sum / Wi_sum) if Wi_sum > 0 else np.nan)
    return pd.Series(hmpi_vals, index=df.index, name="HMPI")

def calculate_mci(df: pd.DataFrame, limits: dict):
    """
    MCI = sum(Ci / Si) across selected metals.
    """
    metals = list(limits.keys())
    def _row_mci(row):
        s = 0.0
        any_val = False
        for m in metals:
            Ci = _safe_get(row, m)
            Si = limits[m]
            if Ci is None or Si is None or Si == 0:
                continue
            s += (Ci / Si)
            any_val = True
        return s if any_val else np.nan
    return df.apply(_row_mci, axis=1).rename("MCI")

def calculate_pi_table(df: pd.DataFrame, limits: dict):
    """
    Returns a DataFrame with PI_<metal> columns (Ci/Si).
    """
    pi = {}
    for m, Si in limits.items():
        col = []
        for _, row in df.iterrows():
            Ci = _safe_get(row, m)
            if Ci is None or Si is None or Si == 0:
                col.append(np.nan)
            else:
                col.append(Ci / Si)
        pi[f"PI_{m}"] = col
    return pd.DataFrame(pi, index=df.index)
