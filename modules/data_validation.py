import pandas as pd
from pathlib import Path

REQUIRED_COLUMNS = [
    "post_id",
    "media_type",
    "content_category",
    "post_datetime",
    "likes",
    "comments",
    "shares",
    "saves",
    "reach",
    "impressions",
    "engagement_rate",
    "hashtags_count",
]



def load_instagram_data(file_path):
    """Load and validate the structure of an Instagram CSV."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The uploaded CSV file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            "The uploaded CSV file could not be parsed. "
            "Please check its structure."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            "The CSV file encoding could not be read. "
            "Please upload a UTF-8 encoded CSV."
        ) from exc

    if df.empty:
        raise ValueError(
            "The CSV contains column headers but no data rows."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    return df




def validate_instagram_data(df):
    """Return a detailed data-quality report without modifying the input."""

    numeric_columns = [
        "likes",
        "comments",
        "shares",
        "saves",
        "reach",
        "impressions",
        "hashtags_count",
        "engagement_rate",
    ]

    report = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_post_ids": (
            int(df["post_id"].duplicated().sum())
            if "post_id" in df.columns
            else None
        ),
        "blank_post_ids": (
            int(
                df["post_id"].astype("string").str.strip()
                .eq("").fillna(False).sum()
            )
            if "post_id" in df.columns
            else None
        ),
        "invalid_negative_metrics": 0,
        "invalid_impressions": 0,
        "invalid_date_values": 0,
        "invalid_numeric_values": 0,
        "infinite_numeric_values": 0,
    }

    for column in numeric_columns:
        if column not in df.columns:
            report[f"invalid_{column}_values"] = None
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        invalid = values.isna() & df[column].notna()
        infinite = values.isin([float("inf"), float("-inf")])

        report[f"invalid_{column}_values"] = int(invalid.sum())
        report["invalid_numeric_values"] += int(invalid.sum())
        report["infinite_numeric_values"] += int(infinite.sum())

        if column != "engagement_rate":
            report["invalid_negative_metrics"] += int(
                (values < 0).sum()
            )

    if "impressions" in df.columns:
        impressions = pd.to_numeric(
            df["impressions"], errors="coerce"
        )
        report["invalid_impressions"] = int(
            (impressions <= 0).sum()
        )

    if "post_datetime" in df.columns:
        dates = pd.to_datetime(df["post_datetime"],format="mixed",errors="coerce")
        report["invalid_date_values"] = int(
            (dates.isna() & df["post_datetime"].notna()).sum()
        )

    return report



def check_engagement_rate(df):
    """Compare stored engagement rate with the documented formula."""
    numeric_columns = [
        "likes",
        "comments",
        "shares",
        "saves",
        "impressions",
        "engagement_rate",
    ]

    data = df[numeric_columns].apply(
        pd.to_numeric, errors="coerce"
    )

    valid = (
        data.notna().all(axis=1)
        & (data["impressions"] > 0)
    )

    expected = (
        data.loc[valid, "likes"]
        + data.loc[valid, "comments"]
        + data.loc[valid, "shares"]
        + data.loc[valid, "saves"]
    ) / data.loc[valid, "impressions"]

    difference = (
        expected - data.loc[valid, "engagement_rate"]
    ).abs()

    return {
        "checked_rows": int(valid.sum()),
        "matching_rows_rounded_4dp": int(
            (difference <= 0.00005 + 1e-12).sum()
        ),
        "max_absolute_difference": (
            float(difference.max())
            if not difference.empty
            else None
        ),
    }
