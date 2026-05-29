from typing import Dict, Any, List
import pandas as pd
import numpy as np
import warnings
from io import StringIO


def _inferred_type(series: pd.Series) -> str:
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return 'string'

    lower_values = non_null.str.lower()
    if lower_values.isin(['true', 'false', '0', '1']).all():
        return 'boolean'

    numeric = pd.to_numeric(non_null, errors='coerce')
    if numeric.notna().all():
        if (numeric % 1 == 0).all():
            return 'integer'
        return 'float'

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            parsed_dates = pd.to_datetime(non_null, errors='coerce')
        parsed_pct = parsed_dates.notna().sum() / len(non_null)
    except Exception:
        parsed_pct = 0.0
    has_non_digit = non_null.str.contains(r'\D').any()
    if parsed_pct >= 0.75 and has_non_digit:
        return 'datetime'

    return 'string'


def profile_from_text(text: str, delimiter: str = ',', top_n: int = 5) -> Dict[str, Any]:
    """Parse CSV text into a pandas DataFrame and compute simple column profiles.

    Returns a dict with `dataset` info and `profile_stats` mapping column -> profile.
    """
    df = pd.read_csv(StringIO(text), sep=delimiter, dtype=object, keep_default_na=True, na_values=['', 'NA', 'N/A'])

    row_count = int(df.shape[0])
    column_count = int(df.shape[1])

    profile_stats: Dict[str, Any] = {}

    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        null_count = int(series.isna().sum())
        null_pct = round((null_count / row_count) * 100, 4) if row_count > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))

        top_values_list: List[Dict[str, Any]] = []
        if non_null.shape[0] > 0:
            vc = non_null.value_counts(dropna=True).head(top_n)
            for val, cnt in vc.items():
                top_values_list.append({"value": str(val), "count": int(cnt), "pct": round((int(cnt) / row_count) * 100, 4)})

        inferred = _inferred_type(series)

        numeric_summary = None
        if inferred in ('integer', 'float'):
            # convert to numeric safely
            num = pd.to_numeric(series, errors='coerce')
            if num.dropna().shape[0] > 0:
                desc = num.dropna().agg(['min', 'quantile', 'median', 'mean', 'max', 'std'])
                q1 = float(num.dropna().quantile(0.25))
                q3 = float(num.dropna().quantile(0.75))
                numeric_summary = {
                    "min": float(num.min()),
                    "q1": q1,
                    "median": float(num.dropna().median()),
                    "mean": float(num.dropna().mean()),
                    "q3": q3,
                    "max": float(num.max()),
                    "std": float(num.dropna().std())
                }

        profile_stats[str(col)] = {
            "name": str(col),
            "inferred_type": inferred,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "top_values": top_values_list,
            "numeric_summary": numeric_summary,
        }

    return {"dataset": {"row_count": row_count, "column_count": column_count}, "profile_stats": profile_stats}
