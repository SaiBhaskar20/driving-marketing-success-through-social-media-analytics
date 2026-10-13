
from os import rename
from unittest import result

import pandas as pd


# Common column names mapped to our standard internal names.
COLUMN_ALIASES = {
    "post_id": ["post_id", "postid", "id", "post_id"],
    "media_type": ["media_type", "media type", "content_type", "post_type"],
    "content_category": [
        "content_category", "content category", "category", "topic"
    ],
    "post_datetime": [
        "post_datetime", "post_date", "post date", "upload_date",
        "uploaded_at", "datetime", "timestamp", "date"
    ],
    "likes": ["likes", "like", "like_count", "likes_count"],
    "comments": ["comments", "comment_count", "comments_count"],
    "shares": ["shares", "share_count", "shares_count"],
    "saves": ["saves", "save_count", "saves_count"],
    "reach": ["reach", "accounts_reached"],
    "impressions": ["impressions", "impression_count", "views"],
    "engagement_rate": [
        "engagement_rate", "engagement rate", "engagementrate"
    ],
    "hashtags": ["hashtags", "hashtag", "tags"],
    "account_type": ["account_type", "account type", "profile_type"],
}


def normalize_column_name(name):
    """Normalize a column name for alias matching."""
    return (
        str(name)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def adapt_csv_columns(df):
    """Map recognized column aliases without inventing missing data."""
    result = df.copy()

    # Match normalized names to original column names.
    original_names = {
        normalize_column_name(column): column
        for column in result.columns
    }

    rename_map = {}

    for standard_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)

            if normalized_alias in original_names:
                original_name = original_names[normalized_alias]

                if original_name != standard_name:
                    # Do not overwrite an existing standard column.
                    if standard_name not in result.columns:
                        rename_map[original_name] = standard_name
                break

    # Keep the original columns and their values unchanged.
    # Add standardized columns only when an alias is recognized.
    for original_name, standard_name in rename_map.items():
        if standard_name not in result.columns:
            result[standard_name] = result[original_name]

    # Normalize engagement rate to a ratio (e.g. 0.1442 = 14.42%).
    # Some files store the rate as a percentage (14.42). Only convert
    # when the supplied rate strongly matches the interaction formula
    # in percentage units and not in ratio units.
    interaction_columns = ["likes", "comments", "shares", "saves"]
    has_formula_inputs = (
        all(col in result.columns for col in interaction_columns)
        and "impressions" in result.columns
    )

    if has_formula_inputs:
        numeric = result[
            interaction_columns + ["impressions"]
        ].apply(pd.to_numeric, errors="coerce")
        valid = (
            numeric.notna().all(axis=1)
            & numeric[interaction_columns].ge(0).all(axis=1)
            & numeric["impressions"].gt(0)
        )
        expected_ratio = pd.Series(float("nan"), index=result.index)
        expected_ratio.loc[valid] = (
            numeric.loc[valid, interaction_columns].sum(axis=1)
            / numeric.loc[valid, "impressions"]
        )

        if "engagement_rate" not in result.columns:
            result["engagement_rate"] = expected_ratio
        else:
            supplied_rate = pd.to_numeric(
                result["engagement_rate"], errors="coerce"
            )
            comparable = valid & supplied_rate.notna()
            if comparable.any():
                raw_error = (
                    supplied_rate.loc[comparable]
                    - expected_ratio.loc[comparable]
                ).abs().median()
                percent_error = (
                    supplied_rate.loc[comparable] / 100
                    - expected_ratio.loc[comparable]
                ).abs().median()
                if percent_error < raw_error:
                    result["engagement_rate"] = supplied_rate / 100
                else:
                    result["engagement_rate"] = supplied_rate

    return result


def get_csv_capabilities(df):
    """Report available data and which analyses can be supported."""
    capabilities = {
        "interaction_metrics": [
            col for col in ["likes", "comments", "shares", "saves"]
            if col in df.columns
        ],
        "has_engagement_rate": "engagement_rate" in df.columns,
        "has_reach": "reach" in df.columns,
        "has_impressions": "impressions" in df.columns,
        "has_posting_date": "post_datetime" in df.columns,
        "has_media_type": "media_type" in df.columns,
        "has_content_category": "content_category" in df.columns,
        "has_hashtags": "hashtags" in df.columns,
    }

    capabilities["can_analyze_interactions"] = bool(
        capabilities["interaction_metrics"]
    )

    capabilities["can_analyze_posting_time"] = (
        capabilities["has_posting_date"]
    )

    capabilities["can_analyze_hashtags"] = (
        capabilities["has_hashtags"]
        and capabilities["has_engagement_rate"]
    )

    return capabilities
