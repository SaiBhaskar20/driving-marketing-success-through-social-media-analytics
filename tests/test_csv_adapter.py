
import pandas as pd

from modules.csv_adapter import (
    adapt_csv_columns,
    get_csv_capabilities,
)


def test_adapter_maps_common_column_aliases():
    df = pd.DataFrame({
        "like_count": [100],
        "comment_count": [10],
        "impression_count": [1000],
    })

    result = adapt_csv_columns(df)

    assert "likes" in result.columns
    assert "comments" in result.columns
    assert "impressions" in result.columns
    assert result.loc[0, "likes"] == 100


def test_adapter_calculates_engagement_rate_when_possible():
    df = pd.DataFrame({
        "likes": [100],
        "comments": [10],
        "shares": [5],
        "saves": [5],
        "impressions": [1000],
    })

    result = adapt_csv_columns(df)

    assert result.loc[0, "engagement_rate"] == 0.12


def test_adapter_does_not_calculate_rate_with_zero_impressions():
    df = pd.DataFrame({
        "likes": [100],
        "comments": [10],
        "shares": [5],
        "saves": [5],
        "impressions": [0],
    })

    result = adapt_csv_columns(df)

    assert pd.isna(result.loc[0, "engagement_rate"])


def test_capabilities_report_missing_posting_date():
    df = pd.DataFrame({
        "likes": [10],
        "hashtags": ["#python"],
    })

    capabilities = get_csv_capabilities(df)

    assert capabilities["can_analyze_interactions"] is True
    assert capabilities["can_analyze_posting_time"] is False
    assert capabilities["can_analyze_hashtags"] is False


def test_adapter_preserves_original_columns():
    df = pd.DataFrame({
        "likes": [10],
        "Caption": ["Sample post"],
        "Hashtags": ["#python"],
    })

    result = adapt_csv_columns(df)

    assert "Caption" in result.columns
    assert "Hashtags" in result.columns


def test_adapter_maps_upload_date_to_post_datetime():
    df = pd.DataFrame({"upload_date": ["2025-01-02 12:30:00"]})
    result = adapt_csv_columns(df)
    assert "post_datetime" in result.columns
    assert result.loc[0, "post_datetime"] == "2025-01-02 12:30:00"


def test_adapter_normalizes_percentage_engagement_rate_to_ratio():
    df = pd.DataFrame({
        "likes": [100],
        "comments": [10],
        "shares": [5],
        "saves": [5],
        "impressions": [1000],
        "engagement_rate": [12.0],
    })
    result = adapt_csv_columns(df)
    assert abs(result.loc[0, "engagement_rate"] - 0.12) < 1e-12


def test_adapter_keeps_ratio_engagement_rate_unchanged():
    df = pd.DataFrame({
        "likes": [100],
        "comments": [10],
        "shares": [5],
        "saves": [5],
        "impressions": [1000],
        "engagement_rate": [0.12],
    })
    result = adapt_csv_columns(df)
    assert abs(result.loc[0, "engagement_rate"] - 0.12) < 1e-12
