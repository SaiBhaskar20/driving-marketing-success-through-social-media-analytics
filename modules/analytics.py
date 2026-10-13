
import pandas as pd




def calculate_overall_kpis(df):
    """Calculate KPIs safely and distinguish weighted from mean rate."""

    def safe_sum(column):
        if column not in df.columns:
            return None
        values = pd.to_numeric(df[column], errors="coerce")
        values = values[values.notna()]
        return float(values.sum()) if not values.empty else None

    def safe_mean(column):
        if column not in df.columns:
            return None
        values = pd.to_numeric(df[column], errors="coerce")
        values = values[values.notna()]
        return float(values.mean()) if not values.empty else None

    interaction_columns = [
        column for column in ["likes", "comments", "shares", "saves"]
        if column in df.columns
    ]
    interaction_totals = [safe_sum(column) for column in interaction_columns]
    total_interactions = (
        sum(value for value in interaction_totals if value is not None)
        if interaction_columns else None
    )

    total_impressions = safe_sum("impressions")
    weighted_rate = (
        total_interactions / total_impressions
        if total_interactions is not None
        and total_impressions is not None
        and total_impressions > 0
        else None
    )
    average_post_rate = safe_mean("engagement_rate")

    return {
        "total_posts": len(df),
        "total_interactions": total_interactions,
        "total_reach": safe_sum("reach"),
        "total_impressions": total_impressions,
        "total_likes": safe_sum("likes"),
        "total_comments": safe_sum("comments"),
        "total_shares": safe_sum("shares"),
        "total_saves": safe_sum("saves"),
        # Keep both names for backward compatibility with existing callers/tests.
        "weighted_engagement_rate": weighted_rate,
        "mean_engagement_rate": average_post_rate,
        "overall_engagement_rate": weighted_rate,
        "average_post_engagement_rate": average_post_rate,
    }



def compare_content_performance(df):
    """Compare performance across media types."""

    result = (
        df.groupby("media_type", dropna=False)
        .agg(
            post_count=("engagement_rate", "count"),
            average_likes=("likes", "mean"),
            average_comments=("comments", "mean"),
            average_shares=("shares", "mean"),
            average_saves=("saves", "mean"),
            average_engagement_rate=("engagement_rate", "mean"),
            median_engagement_rate=("engagement_rate", "median"),
            engagement_rate_std=("engagement_rate", "std"),
        )
        .reset_index()
    )

    return result.sort_values(
        "average_engagement_rate",
        ascending=False,
    )




def analyze_posting_days(df):
    """Compare engagement metrics by day of the week."""

    result = (
        df.groupby("day_of_week", dropna=False)
        .agg(
            post_count=("engagement_rate", "count"),
            average_engagement_rate=("engagement_rate", "mean"),
            median_engagement_rate=("engagement_rate", "median"),
            engagement_rate_std=("engagement_rate", "std"),
            average_likes=("likes", "mean"),
            average_comments=("comments", "mean"),
        )
        .reset_index()
    )

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    result["day_of_week"] = pd.Categorical(
        result["day_of_week"],
        categories=day_order,
        ordered=True,
    )

    return result.sort_values("day_of_week")


def analyze_posting_hours(df):
    """Compare engagement metrics by posting hour."""

    result = (
        df.groupby("post_hour", dropna=False)
        .agg(
            post_count=("engagement_rate", "count"),
            average_engagement_rate=("engagement_rate", "mean"),
            median_engagement_rate=("engagement_rate", "median"),
            engagement_rate_std=("engagement_rate", "std"),
            average_likes=("likes", "mean"),
            average_comments=("comments", "mean"),
        )
        .reset_index()
        .sort_values("post_hour")
    )

    return result


def analyze_hashtags(df):
    """Summarize actual hashtag usage and associated post performance.

    Each hashtag is counted at most once per post. A hashtag-count column
    without actual hashtag names is intentionally not sufficient.
    """
    if "hashtags" not in df.columns or "engagement_rate" not in df.columns:
        return pd.DataFrame()

    columns = ["hashtags", "engagement_rate"]
    optional_metrics = [
        "likes", "comments", "shares", "saves", "impressions", "post_id"
    ]
    columns.extend(column for column in optional_metrics if column in df.columns)
    data = df[columns].copy()
    data["engagement_rate"] = pd.to_numeric(
        data["engagement_rate"], errors="coerce"
    )
    data = data.dropna(subset=["engagement_rate"])
    data["hashtags"] = data["hashtags"].fillna("").astype(str)

    # Extract hashtag tokens, normalize case, and de-duplicate within each post.
    data["hashtags"] = data["hashtags"].str.findall(r"#([\w]+)")
    data["hashtags"] = data["hashtags"].apply(
        lambda tags: sorted({f"#{tag.lower()}" for tag in tags})
    )
    data = data.explode("hashtags")
    data = data[data["hashtags"].notna() & data["hashtags"].ne("")]
    if data.empty:
        return pd.DataFrame()

    aggregations = {
        "post_count": ("engagement_rate", "size"),
        "average_engagement_rate": ("engagement_rate", "mean"),
        "median_engagement_rate": ("engagement_rate", "median"),
        "engagement_rate_std": ("engagement_rate", "std"),
    }
    for column in ["likes", "comments", "shares", "saves", "impressions"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
            aggregations[f"average_{column}"] = (column, "mean")

    result = data.groupby("hashtags", dropna=False).agg(**aggregations).reset_index()
    result["post_count"] = result["post_count"].astype(int)
    return result.sort_values(
        ["post_count", "median_engagement_rate"],
        ascending=[False, False],
    ).reset_index(drop=True)



def estimate_interactions(impressions, historical_median_rate):
    """Estimate interactions using a historical median rate."""
    if impressions <= 0:
        raise ValueError("Impressions must be greater than zero.")

    if not 0 <= historical_median_rate <= 1:
        raise ValueError(
            "Historical engagement rate must be between 0 and 1."
        )

    return round(impressions * historical_median_rate)
