
import pandas as pd
import pytest

from modules.data_validation import (
    REQUIRED_COLUMNS,
    load_instagram_data,
    validate_instagram_data,
    check_engagement_rate,
)


def create_valid_data():
    """Create a small, valid Instagram dataset for testing."""
    return pd.DataFrame({
        "post_id": ["P1", "P2"],
        "media_type": ["reel", "image"],
        "content_category": ["Fashion", "Food"],
        "post_datetime": ["2025-01-01 09:00", "2025-01-02 15:00"],
        "likes": [10, 20],
        "comments": [2, 3],
        "shares": [1, 2],
        "saves": [2, 5],
        "reach": [100, 200],
        "impressions": [200, 400],
        "engagement_rate": [0.075, 0.075],
        "hashtags_count": [3, 5],
    })


def test_load_valid_csv(tmp_path):
    df = create_valid_data()
    file_path = tmp_path / "valid.csv"
    df.to_csv(file_path, index=False)

    loaded = load_instagram_data(file_path)

    assert len(loaded) == 2
    assert all(column in loaded.columns for column in REQUIRED_COLUMNS)


def test_load_missing_file_raises_error(tmp_path):
    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_instagram_data(file_path)


def test_load_csv_with_missing_required_column(tmp_path):
    df = create_valid_data().drop(columns=["likes"])
    file_path = tmp_path / "missing_column.csv"
    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_instagram_data(file_path)


def test_validation_reports_clean_data():
    df = create_valid_data()

    report = validate_instagram_data(df)

    assert report["rows"] == 2
    assert report["columns"] == 12
    assert report["missing_values"] == 0
    assert report["duplicate_rows"] == 0
    assert report["duplicate_post_ids"] == 0
    assert report["invalid_negative_metrics"] == 0
    assert report["invalid_impressions"] == 0


def test_validation_detects_missing_values():
    df = create_valid_data()
    df.loc[0, "likes"] = None

    report = validate_instagram_data(df)

    assert report["missing_values"] == 1
    assert report["invalid_likes_values"] == 0


def test_validation_detects_duplicate_rows_and_ids():
    df = create_valid_data()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    report = validate_instagram_data(df)

    assert report["duplicate_rows"] == 1
    assert report["duplicate_post_ids"] == 1


def test_validation_detects_negative_and_invalid_metrics():
    df = create_valid_data()
    df["shares"] = df["shares"].astype(object)
    df.loc[0, "likes"] = -5
    df.loc[1, "shares"] = "invalid"

    report = validate_instagram_data(df)

    assert report["invalid_negative_metrics"] == 1
    assert report["invalid_shares_values"] == 1


def test_validation_detects_invalid_impressions():
    df = create_valid_data()
    df.loc[0, "impressions"] = 0
    df.loc[1, "impressions"] = -10

    report = validate_instagram_data(df)

    assert report["invalid_impressions"] == 2


def test_engagement_rate_check_with_valid_data():
    df = create_valid_data()

    report = check_engagement_rate(df)

    assert report["checked_rows"] == 2
    assert report["matching_rows_rounded_4dp"] == 2
    assert report["max_absolute_difference"] == pytest.approx(0.0)


def test_engagement_rate_check_detects_mismatch():
    df = create_valid_data()
    df.loc[0, "engagement_rate"] = 0.50

    report = check_engagement_rate(df)

    assert report["checked_rows"] == 2
    assert report["matching_rows_rounded_4dp"] == 1
    assert report["max_absolute_difference"] == pytest.approx(0.425)


def test_engagement_rate_check_skips_invalid_impressions():
    df = create_valid_data()
    df.loc[0, "impressions"] = 0

    report = check_engagement_rate(df)

    assert report["checked_rows"] == 1
    assert report["matching_rows_rounded_4dp"] == 1


def test_validation_detects_invalid_numeric_text():
    df = create_valid_data()
    df["likes"] = df["likes"].astype(object)
    df.loc[0, "likes"] = "invalid"

    report = validate_instagram_data(df)

    assert report["invalid_likes_values"] == 1
    assert report["invalid_numeric_values"] == 1
    assert report["missing_values"] == 0


def test_validation_detects_blank_post_ids():
    df = create_valid_data()
    df.loc[0, "post_id"] = "   "

    report = validate_instagram_data(df)

    assert report["blank_post_ids"] == 1


def test_validation_detects_invalid_dates():
    df = create_valid_data()
    df.loc[0, "post_datetime"] = "not-a-date"

    report = validate_instagram_data(df)

    assert report["invalid_date_values"] == 1


def test_validation_detects_infinite_numeric_values():
    df = create_valid_data()
    df["likes"] = df["likes"].astype(float)

    df.loc[0, "likes"] = float("inf")

    report = validate_instagram_data(df)

    assert report["infinite_numeric_values"] == 1



def test_load_empty_csv_raises_clear_error(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV file is empty"):
        load_instagram_data(file_path)


def test_load_csv_with_headers_but_no_rows(tmp_path):
    df = create_valid_data().iloc[0:0]
    file_path = tmp_path / "no_rows.csv"
    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="no data rows"):
        load_instagram_data(file_path)


def test_load_malformed_csv_raises_clear_error(tmp_path):
    file_path = tmp_path / "malformed.csv"
    file_path.write_text(
        'post_id,likes\nP1,"10\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="could not be parsed"):
        load_instagram_data(file_path)
