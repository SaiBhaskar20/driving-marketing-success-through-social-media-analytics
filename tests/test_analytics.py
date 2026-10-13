import numpy as np
import pandas as pd

from modules.analytics import (
    calculate_overall_kpis,
    compare_content_performance,
    analyze_posting_days,
    analyze_posting_hours,
    analyze_hashtags,
)


def create_sample_data():
    return pd.DataFrame({
        "post_id": ["P1", "P2", "P3"],
        "media_type": ["reel", "image", "reel"],
        "day_of_week": ["Monday", "Tuesday", "Monday"],
        "post_hour": [9, 15, 9],
        "likes": [100, 50, 150],
        "comments": [10, 5, 15],
        "shares": [5, 2, 10],
        "saves": [5, 3, 10],
        "reach": [500, 300, 700],
        "impressions": [1000, 600, 2000],
        "engagement_rate": [0.12, 0.10, 0.0925],
    })


def test_overall_kpis():
    df = create_sample_data()
    result = calculate_overall_kpis(df)

    assert result["total_posts"] == 3
    assert result["total_likes"] == 300
    assert result["total_interactions"] == 365
    assert abs(
        result["overall_engagement_rate"] - (365 / 3600)
    ) < 1e-10


def test_content_comparison():
    df = create_sample_data()
    result = compare_content_performance(df)

    assert set(result["media_type"]) == {"reel", "image"}
    assert result["post_count"].sum() == 3


def test_posting_day_analysis():
    df = create_sample_data()
    result = analyze_posting_days(df)

    assert result["post_count"].sum() == 3
    assert list(result["day_of_week"].astype(str)) == [
        "Monday", "Tuesday"
    ]


def test_posting_hour_analysis():
    df = create_sample_data()
    result = analyze_posting_hours(df)

    assert result["post_count"].sum() == 3
    assert list(result["post_hour"]) == [9, 15]



def test_content_comparison_includes_median_and_std():
    df = create_sample_data()
    result = compare_content_performance(df)

    reel = result.loc[result["media_type"] == "reel"].iloc[0]
    image = result.loc[result["media_type"] == "image"].iloc[0]

    # Reel rates: 0.12 and 0.0925
    assert abs(reel["median_engagement_rate"] - 0.10625) < 1e-10
    assert abs(reel["engagement_rate_std"] - 0.019445436) < 1e-8

    # Image has only one post, so sample standard deviation is undefined.
    assert abs(image["median_engagement_rate"] - 0.10) < 1e-10
    assert pd.isna(image["engagement_rate_std"])


def test_posting_day_includes_median_and_std():
    df = create_sample_data()
    result = analyze_posting_days(df)

    monday = result.loc[
        result["day_of_week"].astype(str) == "Monday"
    ].iloc[0]

    tuesday = result.loc[
        result["day_of_week"].astype(str) == "Tuesday"
    ].iloc[0]

    assert abs(monday["median_engagement_rate"] - 0.10625) < 1e-10
    assert abs(monday["engagement_rate_std"] - 0.019445436) < 1e-8

    assert abs(tuesday["median_engagement_rate"] - 0.10) < 1e-10
    assert pd.isna(tuesday["engagement_rate_std"])


def test_posting_hour_includes_median_and_std():
    df = create_sample_data()
    result = analyze_posting_hours(df)

    assert "median_engagement_rate" in result.columns
    assert "engagement_rate_std" in result.columns

    # Each hour has only one post in this sample.
    assert result.loc[
    result["post_hour"] == 15,
    "engagement_rate_std",].isna().all()


def test_analysis_handles_single_post():
    df = create_sample_data().iloc[[0]].copy()

    content = compare_content_performance(df)
    days = analyze_posting_days(df)
    hours = analyze_posting_hours(df)

    assert content.iloc[0]["post_count"] == 1
    assert days.iloc[0]["post_count"] == 1
    assert hours.iloc[0]["post_count"] == 1

    assert pd.isna(content.iloc[0]["engagement_rate_std"])
    assert pd.isna(days.iloc[0]["engagement_rate_std"])
    assert pd.isna(hours.iloc[0]["engagement_rate_std"])



def test_hashtag_analysis_returns_empty_without_hashtag_names():
    df = create_sample_data()

    result = analyze_hashtags(df)

    assert result.empty


def test_hashtag_analysis_compares_actual_hashtags():
    df = pd.DataFrame({
        "hashtags": ["#Python #DataScience", "#python", "#AI"],
        "engagement_rate": [0.10, 0.20, 0.05],
    })

    result = analyze_hashtags(df)

    python_result = result[result["hashtags"] == "#python"]

    assert len(python_result) == 1
    assert python_result.iloc[0]["post_count"] == 2
    assert abs(
        python_result.iloc[0]["average_engagement_rate"] - 0.15
    ) < 1e-10


def test_hashtag_analysis_handles_empty_hashtags():
    df = pd.DataFrame({
        "hashtags": ["", None, "   "],
        "engagement_rate": [0.10, 0.20, 0.05],
    })

    result = analyze_hashtags(df)

    assert result.empty



import pytest

from modules.analytics import estimate_interactions


def test_estimate_interactions_with_valid_values():
    assert estimate_interactions(10000, 0.0431) == 431


def test_estimate_interactions_rounds_result():
    assert estimate_interactions(1000, 0.1236) == 124


def test_estimate_interactions_rejects_zero_impressions():
    with pytest.raises(ValueError):
        estimate_interactions(0, 0.05)


def test_estimate_interactions_rejects_negative_impressions():
    with pytest.raises(ValueError):
        estimate_interactions(-100, 0.05)


def test_estimate_interactions_rejects_invalid_rate():
    with pytest.raises(ValueError):
        estimate_interactions(1000, 1.5)


def test_estimate_interactions_accepts_zero_rate():
    assert estimate_interactions(1000, 0) == 0


def test_hashtag_analysis_counts_each_hashtag_once_per_post():
    df = pd.DataFrame({
        "post_id": ["P1", "P2"],
        "hashtags": ["#Python #python #DataScience", "#python"],
        "engagement_rate": [0.10, 0.20],
        "likes": [10, 30],
        "comments": [2, 4],
        "impressions": [100, 150],
    })

    result = analyze_hashtags(df)
    python = result.loc[result["hashtags"] == "#python"].iloc[0]
    data_science = result.loc[
        result["hashtags"] == "#datascience"
    ].iloc[0]

    assert python["post_count"] == 2
    assert abs(python["average_engagement_rate"] - 0.15) < 1e-10
    assert python["average_likes"] == 20
    assert data_science["post_count"] == 1


def test_hashtag_analysis_returns_empty_when_no_actual_hashtag_tokens():
    df = pd.DataFrame({
        "hashtags": ["python data science", "", None],
        "engagement_rate": [0.1, 0.2, 0.3],
    })
    assert analyze_hashtags(df).empty
