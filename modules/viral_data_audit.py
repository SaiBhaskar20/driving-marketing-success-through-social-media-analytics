from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = (
    PROJECT_DIR / "data" / "social_media_viral_content_dataset.csv"
)


def audit_viral_dataset(file_path=DATASET_PATH):
    df = pd.read_csv(file_path)

    required_columns = [
        "post_id",
        "platform",
        "content_type",
        "topic",
        "post_datetime",
        "hashtags",
        "views",
        "likes",
        "comments",
        "shares",
        "engagement_rate",
        "is_viral",
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    print("\n--- DATASET OVERVIEW ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Duplicate post IDs:", int(df["post_id"].duplicated().sum()))
    print("Missing values:\n", df.isna().sum().to_string())

    print("\n--- PLATFORM DISTRIBUTION ---")
    print(df["platform"].value_counts(dropna=False).to_string())

    print("\n--- VIRAL LABEL DISTRIBUTION ---")
    print(df["is_viral"].value_counts(dropna=False).to_string())
    print("Viral label values:", sorted(df["is_viral"].dropna().unique()))

    numeric_columns = [
        "views",
        "likes",
        "comments",
        "shares",
        "engagement_rate",
    ]

    numeric = df[numeric_columns].apply(
        pd.to_numeric, errors="coerce"
    )

    print("\n--- NUMERIC QUALITY ---")
    print("Invalid numeric values:\n", numeric.isna().sum().to_string())
    print("Infinite numeric values:\n",
          np.isinf(numeric).sum().to_string())
    print("Negative values:\n",
          (numeric < 0).sum().to_string())
    print("Numeric summary:\n", numeric.describe().to_string())

    valid = (
        numeric[["views", "likes", "comments", "shares"]]
        .notna()
        .all(axis=1)
        & (numeric["views"] > 0)
    )

    expected_rate = (
        numeric.loc[valid, "likes"]
        + numeric.loc[valid, "comments"]
        + numeric.loc[valid, "shares"]
    ) / numeric.loc[valid, "views"]

    difference = (
        expected_rate - numeric.loc[valid, "engagement_rate"]
    ).abs()

    print("\n--- ENGAGEMENT RATE FORMULA CHECK ---")
    print("Rows checked:", int(valid.sum()))
    print("Rows matching (tolerance 0.0001):",
          int((difference <= 0.0001).sum()))
    print("Maximum difference:",
          float(difference.max()) if not difference.empty else None)

    print("\n--- DATE RANGE ---")
    dates = pd.to_datetime(df["post_datetime"], errors="coerce")
    print("Invalid dates:", int(dates.isna().sum()))
    print("Earliest date:", dates.min())
    print("Latest date:", dates.max())

    print("\n--- VIRAL LABEL BY PLATFORM ---")
    print(
        pd.crosstab(
            df["platform"],
            df["is_viral"],
            normalize="index",
        ).round(3).to_string()
    )

    
    print("\n--- POSSIBLE LABEL LEAKAGE CHECK ---")

    metrics = [
        "views",
        "likes",
        "comments",
        "shares",
        "engagement_rate",
    ]

    summary = (
        df.groupby("is_viral")[metrics]
        .agg(["mean", "median", "std"])
        .round(4)
    )

    print("Metric distributions grouped by viral label:")
    print("Label 0 = Non-viral, Label 1 = Viral")
    print(summary.to_string())

    print("\n--- MEAN DIFFERENCE (VIRAL - NON-VIRAL) ---")

    means = df.groupby("is_viral")[metrics].mean()

    for col in metrics:
        if 0 in means.index and 1 in means.index:
            difference = means.loc[1, col] - means.loc[0, col]

            print(
                f"{col}: "
                f"non-viral mean={means.loc[0, col]:.4f}, "
                f"viral mean={means.loc[1, col]:.4f}, "
                f"difference={difference:.4f}"
            )

    return df


if __name__ == "__main__":
    report_path = PROJECT_DIR / "data" / "viral_audit_report.txt"

    import contextlib

    with open(report_path, "w", encoding="utf-8") as report_file:
        with contextlib.redirect_stdout(report_file):
            audit_viral_dataset()

    print(f"Audit report saved to: {report_path}")
