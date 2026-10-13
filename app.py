from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from modules.data_validation import (
    load_instagram_data,
    validate_instagram_data,
    check_engagement_rate,  

)

from modules.analytics import (
    calculate_overall_kpis,
    compare_content_performance,
    analyze_posting_days,
    analyze_posting_hours,
    analyze_hashtags,
    estimate_interactions,
)

from modules.csv_adapter import (
    adapt_csv_columns,
    get_csv_capabilities,
)

PROJECT_DIR = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_DIR / "data" / "Instagram_Analytics.csv"

st.set_page_config(

    page_title="Social Media Analytics",

    page_icon="📊",

    layout="wide",

)



st.title("📊 Driving Marketing Success Through Social Media Analytics")

st.caption("Instagram content performance and engagement insights")



@st.cache_data

def load_demo_data():

    df = load_instagram_data(DATASET_PATH)



    # Exclude the unverified label from core analytics

    if "performance_bucket_label" in df.columns:

        df = df.drop(columns=["performance_bucket_label"])



    df["post_datetime"] = pd.to_datetime(

        df["post_datetime"], errors="coerce"

    )



    for column in [

        "likes", "comments", "shares", "saves",

        "reach", "impressions", "engagement_rate",

        "hashtags_count", "post_hour",

    ]:

        df[column] = pd.to_numeric(df[column], errors="coerce")



    return df





# Choose the data source

st.sidebar.header("Data Source")



data_source = st.sidebar.radio(

    "Choose how to analyse data",

    ["Try Demo", "Upload Own CSV"],

)



if data_source == "Try Demo":

    try:

        df = load_demo_data()

        st.sidebar.success("Demo dataset loaded")

    except Exception as error:

        st.error(f"Unable to load demo dataset: {error}")

        st.stop()



else:

    uploaded_file = st.sidebar.file_uploader(

        "Upload your Instagram CSV",

        type=["csv"],

        help=(

            "Upload a CSV containing post metrics. "

            "Your file is processed in this session only."

        ),

    )



    if uploaded_file is None:

        st.info(

            "Upload a CSV from the sidebar to start analysing your data."

        )

        st.stop()



    try:



        try:

            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")

        except UnicodeDecodeError:

            uploaded_file.seek(0)

            df = pd.read_csv(uploaded_file, encoding="cp1252")





        # Required columns for the core analytics dashboard

        required_columns = [

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

        ]





        # Normalize recognized column names before checking compatibility.

        df = adapt_csv_columns(df)
        st.write("CSV columns:", df.columns.tolist())

        if "post_datetime" in df.columns:
            st.write("Sample dates:", df["post_datetime"].head(5).tolist())
        else:
            st.write("No post_datetime column found.")
        capabilities = get_csv_capabilities(df)



        # Report which important fields are unavailable.

        optional_fields = {

        "post_id": "Post ID",

        "media_type": "Media type",

        "content_category": "Content category",

        "post_datetime": "Posting date/time",

        "likes": "Likes",

        "comments": "Comments",

        "shares": "Shares",

        "saves": "Saves",

        "reach": "Reach",

        "impressions": "Impressions",

        "engagement_rate": "Engagement rate",

        }



        missing_fields = [

        label

        for column, label in optional_fields.items()

        if column not in df.columns

        ]



        if missing_fields:

            st.warning(

            "Some fields are unavailable in this CSV: "

            + ", ".join(missing_fields)

            + ". Only analyses supported by the available data can be shown."

            )



        if not capabilities["can_analyze_interactions"]:

            st.error(

            "This CSV does not contain recognized interaction metrics "

            "(likes, comments, shares, or saves). "

            "Please upload a compatible social-media dataset."

            )

            st.stop()





        # Remove unverified labels from core analytics.

        if "performance_bucket_label" in df.columns:

            df = df.drop(columns=["performance_bucket_label"])



        # Process posting dates only when the source provides them.

        # An all-NaT internal column lets date-based sections show an

        # unavailable message instead of crashing; no dates are invented.

        if "post_datetime" not in df.columns:

            df["post_datetime"] = pd.Series(

                pd.NaT, index=df.index, dtype="datetime64[ns]"

            )



        if "post_datetime" in df.columns:

            df["post_datetime"] = pd.to_datetime(

                df["post_datetime"],

                format="mixed",

                errors="coerce",

            )



            invalid_dates = int(df["post_datetime"].isna().sum())



            if invalid_dates:

                st.warning(

                    f"{invalid_dates} rows have missing or invalid "

                    "posting dates. These rows cannot be used for "

                    "posting-day or posting-hour analysis."

                )



            df["post_hour"] = df["post_datetime"].dt.hour

            df["day_of_week"] = df["post_datetime"].dt.day_name()

        else:

            st.warning(

                "Posting date/time is unavailable. "

                "Posting-day and posting-hour analysis cannot be performed."

            )



        # Add a neutral category only when the source has no such field.

        # This does not claim the original category is known.

        for column in ["media_type", "content_category", "account_type"]:

            if column not in df.columns:

                df[column] = "Unknown"

                st.warning(

                    f"'{column}' is unavailable. "

                    "The dashboard will use 'Unknown' for this field."

                )

            else:

                df[column] = (

                    df[column].fillna("Unknown").astype(str)

                )



        # Convert only numeric columns that actually exist.

        numeric_columns = [

            "likes",

            "comments",

            "shares",

            "saves",

            "reach",

            "impressions",

            "engagement_rate",

            "hashtags_count",

        ]



        present_numeric_columns = [

            column for column in numeric_columns

            if column in df.columns

        ]



        for column in present_numeric_columns:

            df[column] = pd.to_numeric(

                df[column], errors="coerce"

            )



        # Warn about invalid values rather than rejecting the entire CSV.

        invalid_counts = {

            column: int(df[column].isna().sum())

            for column in present_numeric_columns

            if df[column].isna().any()

        }



        if invalid_counts:

            st.warning(

                "Some numeric fields contain missing or non-numeric "

                f"values: {invalid_counts}. These rows need to be "

                "excluded from analyses that require those fields."

            )



        negative_counts = {

            column: int((df[column] < 0).sum())

            for column in present_numeric_columns

            if column != "engagement_rate"

            and (df[column].dropna() < 0).any()

        }



        if negative_counts:

            st.warning(

                "Negative metric values were found: "

                f"{negative_counts}. Review these values before relying "

                "on results."

            )



        # Calculate engagement rate only when all required source

        # metrics exist. The adapter handles this calculation.

        if "engagement_rate" not in df.columns:

            st.warning(

                "Engagement rate is unavailable because the required "

                "interaction metrics and impressions are not all present."

            )



        # Derive hashtag count only from actual hashtag names.

        if "hashtags_count" not in df.columns and "hashtags" in df.columns:

            df["hashtags_count"] = (

                df["hashtags"]

                .fillna("")

                .astype(str)

                .str.findall(r"#\w+")

                .str.len()

            )



        st.success(

            f"CSV loaded: {len(df):,} rows. "

            "Available fields have been inspected."

        )





        # CSV data-quality report

        validation_report = validate_instagram_data(df)



        with st.expander("CSV Data Quality Report", expanded=True):

            col1, col2, col3 = st.columns(3)



            col1.metric(

                "Rows checked",

                f"{validation_report['rows']:,}",

            )

            col2.metric(

                "Missing values",

                f"{validation_report['missing_values']:,}",

            )

            col3.metric(

                "Duplicate rows",

                f"{validation_report['duplicate_rows']:,}",

            )



            st.write(

                "Duplicate post IDs:",

                validation_report["duplicate_post_ids"],

            )

            st.write(

                "Blank post IDs:",

                validation_report["blank_post_ids"],

            )

            st.write(

                "Invalid numeric values:",

                validation_report["invalid_numeric_values"],

            )

            st.write(

                "Infinite numeric values:",

                validation_report["infinite_numeric_values"],

            )

            st.write(

                "Negative metrics:",

                validation_report["invalid_negative_metrics"],

            )

            st.write(

                "Invalid impressions:",

                validation_report["invalid_impressions"],

            )

            st.write(

                "Invalid dates:",

                validation_report["invalid_date_values"],

            )



            engagement_report = check_engagement_rate(df)



            st.subheader("Engagement Rate Audit")

            st.write(

                "Rows checked:",

                engagement_report["checked_rows"],

            )

            st.write(

                "Rows matching the formula (rounded to 4 decimals):",

                engagement_report["matching_rows_rounded_4dp"],

            )

            st.write(

                "Maximum absolute difference:",

                engagement_report["max_absolute_difference"],



            )



            # Overall data-quality status

            quality_issues = []



            if validation_report["missing_values"] > 0:

                quality_issues.append("Missing values found")



            if validation_report["duplicate_rows"] > 0:

                quality_issues.append("Duplicate rows found")



            if (validation_report.get("duplicate_post_ids") or 0) > 0:

                quality_issues.append("Duplicate post IDs found")



            if (validation_report.get("blank_post_ids") or 0) > 0:

                quality_issues.append("Blank post IDs found")



            if validation_report["invalid_numeric_values"] > 0:

                quality_issues.append("Invalid numeric values found")



            if validation_report["infinite_numeric_values"] > 0:

                quality_issues.append("Infinite numeric values found")



            if validation_report["invalid_negative_metrics"] > 0:

                quality_issues.append("Negative metric values found")



            if validation_report["invalid_impressions"] > 0:

                quality_issues.append("Zero or negative impressions found")



            if validation_report["invalid_date_values"] > 0:

                quality_issues.append("Invalid posting dates found")



            if (

                engagement_report["checked_rows"] > 0

                and engagement_report["matching_rows_rounded_4dp"]

                < engagement_report["checked_rows"]

            ):

                quality_issues.append(

                    "Engagement rates do not all match the expected formula"

                )



            st.subheader("Overall Data Quality Status")



            if quality_issues:

                st.warning(

                    "Warnings found. Review the issues below before "

                    "relying on the marketing recommendations."

                )



                for issue in quality_issues:

                    st.markdown(f"- {issue}")

            else:

                st.success(

                    "All current data-quality checks passed. "

                    "This does not guarantee that the dataset is "

                    "complete or free from every possible issue."

                )







    except Exception as error:

        st.error(f"Could not read the uploaded CSV: {error}")

        st.stop()





# Sidebar filters

st.sidebar.header("Dashboard Filters")



media_options = sorted(df["media_type"].dropna().unique())

selected_media = st.sidebar.multiselect(

    "Media Type",

    options=media_options,

    default=media_options,

)



category_options = sorted(df["content_category"].dropna().unique())

selected_categories = st.sidebar.multiselect(

    "Content Category",

    options=category_options,

    default=category_options,

)



account_options = sorted(df["account_type"].dropna().unique())

selected_accounts = st.sidebar.multiselect(

    "Account Type",

    options=account_options,

    default=account_options,

)





# Keep the filtered data unchanged for reporting.

filtered_df = df[

    df["media_type"].isin(selected_media)

    & df["content_category"].isin(selected_categories)

    & df["account_type"].isin(selected_accounts)

].copy()





# Create a separate dataset for safe metric-based analysis.

analysis_df = filtered_df.copy()



required_metric_columns = [

    "likes",

    "comments",

    "shares",

    "saves",

    "reach",

    "impressions",

    "engagement_rate",

]



available_metric_columns = [

    column

    for column in required_metric_columns

    if column in analysis_df.columns

]



# Convert only metric columns that actually exist.

numeric_data = analysis_df[available_metric_columns].apply(

    pd.to_numeric,

    errors="coerce",

)



# Keep rows with valid, finite values in available metrics.

if not numeric_data.empty:

    finite_metrics = numeric_data.apply(

        lambda column: (

            column.notna()

            & column.map(

                lambda value: (

                    pd.notna(value)

                    and value not in (float("inf"), float("-inf"))

                )

            )

        )

    )

    valid_metric_rows = finite_metrics.all(axis=1)

else:

    valid_metric_rows = pd.Series(

        True,

        index=analysis_df.index,

    )



# Validate non-negative values only for available count metrics.

non_negative_columns = [

    column

    for column in [

        "likes",

        "comments",

        "shares",

        "saves",

        "reach",

        "impressions",

    ]

    if column in numeric_data.columns

]



if non_negative_columns:

    non_negative_metrics = (

        numeric_data[non_negative_columns]

        .ge(0)

        .all(axis=1)

    )

else:

    non_negative_metrics = pd.Series(

        True,

        index=analysis_df.index,

    )



# Positive impressions are required only when that column exists.

if "impressions" in numeric_data.columns:

    valid_impressions = numeric_data["impressions"] > 0

else:

    valid_impressions = pd.Series(

        True,

        index=analysis_df.index,

    )



safe_rows = (

    valid_metric_rows

    & non_negative_metrics

    & valid_impressions

)



excluded_rows = int((~safe_rows).sum())

analysis_df = analysis_df.loc[safe_rows].copy()



# Replace available metrics with their numeric versions.

if available_metric_columns:

    analysis_df[available_metric_columns] = numeric_data.loc[

        safe_rows,

        available_metric_columns,

    ]



if excluded_rows:

    st.warning(

        f"{excluded_rows} rows were excluded from metric analysis "

        "because available metrics contained missing, invalid, "

        "infinite, negative, or non-positive impression values."

    )



if not available_metric_columns:

    st.warning(

        "No recognized numeric engagement metrics are available. "

        "Metric-based analysis cannot be displayed for this CSV."

    )





# Ensure numeric columns use numeric values in calculations.

analysis_df[available_metric_columns] = numeric_data.loc[

    safe_rows, available_metric_columns

]



if excluded_rows > 0:

    st.warning(

        f"{excluded_rows:,} of {len(filtered_df):,} filtered posts "

        "were excluded from metric-based analysis because of "

        "invalid, missing, infinite, or unsuitable metric values."

    )

else:

    st.success(

        "All filtered posts passed the current metric checks."

    )



st.caption(

    "Date quality is handled separately so a valid post's engagement "

    "metrics can still be used when its posting date is invalid."

)





if filtered_df.empty:

    st.warning("No posts match the selected filters.")

    st.stop()



# KPI cards

kpis = calculate_overall_kpis(analysis_df)



st.subheader("Overall Performance")



c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Posts", f'{kpis["total_posts"]:,}')

c2.metric("Total Interactions", f'{kpis["total_interactions"]:,}')

reach_value = kpis.get("total_reach")



c3.metric(

    "Total Reach",

    f"{reach_value:,.0f}" if reach_value is not None else "N/A"

)

impressions_value = kpis.get("total_impressions")



c4.metric(

    "Total Impressions",

    f"{impressions_value:,.0f}"

    if impressions_value is not None

    else "N/A"

)



c5, c6, c7, c8 = st.columns(4)

c5.metric("Total Likes", f'{kpis["total_likes"]:,}')

c6.metric("Total Comments", f'{kpis["total_comments"]:,}')

c7.metric("Total Shares", f'{kpis["total_shares"]:,}')

c8.metric("Total Saves", f'{kpis["total_saves"]:,}')



st.metric(

    "Weighted Engagement Rate",

    f'{kpis["overall_engagement_rate"]:.2%}',

    help="Total interactions divided by total impressions.",

)



st.caption(

    f'Average of individual post engagement rates: '

    f'{kpis["average_post_engagement_rate"]:.2%}'

)



st.divider()



# Content performance

st.subheader("Content Performance Comparison")



content_result = compare_content_performance(analysis_df)



content_chart = px.bar(

    content_result,

    x="media_type",

    y="average_engagement_rate",

    color="media_type",

    hover_data=["post_count", "average_likes", "average_comments"],

    labels={

        "media_type": "Media Type",

        "average_engagement_rate": "Average Engagement Rate",

    },

    title="Average Engagement Rate by Media Type",

)



content_chart.update_yaxes(tickformat=".1%")

st.plotly_chart(content_chart, width="stretch")

st.dataframe(content_result, width="stretch")



st.divider()





# Posting-day analysis

st.subheader("Posting Day Analysis")



day_analysis_df = analysis_df.copy()



day_analysis_df["post_datetime"] = pd.to_datetime(

    day_analysis_df["post_datetime"],

    format="mixed",

    errors="coerce",

)



# Exclude posts with invalid or missing dates from day analysis only.

day_analysis_df = day_analysis_df.dropna(

    subset=["post_datetime"]

).copy()



# Derive weekday from the validated timestamp to avoid stale labels.

day_analysis_df["day_of_week"] = (

    day_analysis_df["post_datetime"].dt.day_name()

)



if day_analysis_df.empty:

    st.info(

        "Posting-day analysis is unavailable because no valid "

        "posting dates remain after validation."

    )

else:

    day_result = analyze_posting_days(day_analysis_df)



    if day_result.empty:

        st.info("Not enough data to compare posting days.")

    else:

        day_chart = px.bar(

            day_result,

            x="day_of_week",

            y="average_engagement_rate",

            hover_data=[

                "post_count",

                "average_likes",

                "average_comments",

            ],

            labels={

                "day_of_week": "Day of Week",

                "average_engagement_rate": "Average Engagement Rate",

            },

            title="Average Engagement Rate by Day",

        )



        day_chart.update_yaxes(tickformat=".1%")

        st.plotly_chart(day_chart, width="stretch")



        st.caption(

            f"Posting-day analysis uses {len(day_analysis_df):,} posts "

            "with valid posting dates and valid engagement metrics."

        )



st.divider()







# Posting-hour analysis

st.subheader("Posting Hour Analysis")



hour_analysis_df = analysis_df.copy()



# Parse timestamps safely and derive the hour from the validated datetime.

hour_analysis_df["post_datetime"] = pd.to_datetime(

    hour_analysis_df["post_datetime"],

    format="mixed",

    errors="coerce",

)



hour_analysis_df = hour_analysis_df.dropna(

    subset=["post_datetime"]

).copy()



hour_analysis_df["post_hour"] = (

    hour_analysis_df["post_datetime"].dt.hour

)



if hour_analysis_df.empty:

    st.info(

        "Posting-hour analysis is unavailable because no valid "

        "posting dates remain after validation."

    )

else:

    hour_result = analyze_posting_hours(hour_analysis_df)



    if hour_result.empty:

        st.info("Not enough valid data to compare posting hours.")

    else:

        hour_chart = px.line(

            hour_result,

            x="post_hour",

            y="average_engagement_rate",

            markers=True,

            hover_data=[

                "post_count",

                "average_likes",

                "average_comments",

            ],

            labels={

                "post_hour": "Posting Hour (24-hour format)",

                "average_engagement_rate": "Average Engagement Rate",

            },

            title="Average Engagement Rate by Posting Hour",

        )



        hour_chart.update_xaxes(

            dtick=1,

            tick0=0,

            range=[-0.5, 23.5],

            tickmode="linear",

        )

        hour_chart.update_yaxes(tickformat=".1%")

        st.plotly_chart(hour_chart, width="stretch")



        st.caption(

            f"Posting-hour analysis uses {len(hour_analysis_df):,} "

            "posts with valid posting dates and engagement metrics."

        )



st.caption(

    "These charts show associations in the supplied dataset. "

    "They do not prove that a particular content type or posting time "

    "causes higher engagement."

)





# Hashtag analysis

st.divider()

st.subheader("Hashtag Performance Analysis")



hashtag_result = analyze_hashtags(analysis_df)



if not hashtag_result.empty:

    st.caption(

        "Hashtag metrics summarize posts containing each hashtag. "

        "They show historical association, not proof that a hashtag caused engagement."

    )



    hashtag_controls = st.columns([1, 1])

    minimum_posts = hashtag_controls[0].selectbox(

        "Minimum posts per hashtag",

        options=[1, 2, 3, 5, 10],

        index=2,

        key="hashtag_minimum_posts",

        help="Higher minimums reduce conclusions based on very small samples.",

    )

    sort_label = hashtag_controls[1].selectbox(

        "Rank hashtags by",

        options=["Median engagement", "Average engagement", "Post count"],

        key="hashtag_sort_method",

    )



    visible_hashtags = hashtag_result[

        hashtag_result["post_count"] >= minimum_posts

    ].copy()

    sort_columns = {

        "Median engagement": "median_engagement_rate",

        "Average engagement": "average_engagement_rate",

        "Post count": "post_count",

    }

    sort_column = sort_columns[sort_label]

    visible_hashtags = visible_hashtags.sort_values(

        sort_column, ascending=False

    ).reset_index(drop=True)



    h1, h2, h3 = st.columns(3)

    h1.metric("Unique Hashtags", f"{len(hashtag_result):,}")

    h2.metric("Hashtag–Post Associations", f"{int(hashtag_result['post_count'].sum()):,}")

    h3.metric("Hashtags Meeting Minimum", f"{len(visible_hashtags):,}")



    if visible_hashtags.empty:

        st.info(

            "No hashtags meet this minimum post count. Lower the minimum "

            "to explore hashtags with fewer posts."

        )

    else:

        st.dataframe(

            visible_hashtags,

            width="stretch",

            hide_index=True,

        )



        chart_data = visible_hashtags.head(15).sort_values(sort_column)

        chart_titles = {

            "median_engagement_rate": "Median Engagement Rate by Hashtag",

            "average_engagement_rate": "Average Engagement Rate by Hashtag",

            "post_count": "Most Frequently Used Hashtags",

        }

        chart = px.bar(

            chart_data,

            x=sort_column,

            y="hashtags",

            orientation="h",

            hover_data=[

                column for column in [

                    "post_count", "average_engagement_rate",

                    "median_engagement_rate", "average_likes",

                    "average_comments", "average_impressions",

                ] if column in chart_data.columns

            ],

            labels={

                "hashtags": "Hashtag",

                "post_count": "Posts containing hashtag",

                "average_engagement_rate": "Average Engagement Rate",

                "median_engagement_rate": "Median Engagement Rate",

            },

            title=chart_titles[sort_column],

        )

        if sort_column != "post_count":

            chart.update_xaxes(tickformat=".1%")

        st.plotly_chart(chart, width="stretch")



        st.caption(

            f"Only hashtags appearing in at least {minimum_posts} posts are shown. "

            "Repeated use of the same hashtag within one post is counted once."

        )

else:

    st.info(

        "Hashtag analysis is unavailable because this dataset does not contain "

        "actual hashtag names and a usable engagement-rate column. A hashtag "

        "count alone is not enough to compare individual hashtags."

    )





# Download filtered data

st.subheader("Export Filtered Data")



csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")



st.download_button(

    label="Download filtered posts as CSV",

    data=csv_bytes,

    file_name="instagram_analytics_filtered.csv",

    mime="text/csv",

)



# Evidence-based recommendations

st.divider()

st.subheader("Marketing Recommendations")



st.caption(

    "Recommendations are based on the currently filtered posts. "

    "They show observed patterns, not guaranteed future results."

)



# Best-performing content type



content_result = compare_content_performance(analysis_df)



if not content_result.empty:

    best_content = content_result.iloc[0]



    post_count = int(best_content["post_count"])

    average_rate = best_content["average_engagement_rate"]

    median_rate = best_content["median_engagement_rate"]

    std_rate = best_content["engagement_rate_std"]



    st.markdown(

        f"**Content type to investigate:** "

        f"{best_content['media_type']}"

    )



    col1, col2, col3 = st.columns(3)



    col1.metric("Posts analysed", f"{post_count:,}")



    col2.metric(

        "Average engagement rate",

        f"{average_rate:.2%}",

    )



    col3.metric(

        "Median engagement rate",

        f"{median_rate:.2%}",

    )



    if post_count < 10:

        st.warning(

            "Low sample size: this is a preliminary insight. "

            "Analyse more posts before making a marketing decision."

        )

    else:

        st.info(

            f"This comparison is based on {post_count:,} posts. "

            "The sample size supports an initial comparison, "

            "but does not guarantee that the pattern will continue."

        )



    if pd.notna(std_rate):

        st.write(

            f"**Engagement variability:** {std_rate:.2%} "

            "(standard deviation)."

        )

    else:

        st.write(

            "**Engagement variability:** Cannot be estimated "

            "from a single valid post."

        )



    st.write(

        f"**Why investigate this?** Its average engagement rate "

        f"was the highest among the content types in the "

        f"currently filtered data."

    )



    st.write(

        "**Next action:** Test this content type against another "

        "content type using comparable topics and posting times. "

        "Compare the results again before changing your strategy."

    )



else:

    st.info("Not enough data to compare content types.")







# Best-performing posting day
day_recommendation_df = analysis_df.copy()
if "post_datetime" not in day_recommendation_df.columns:
    day_recommendation_df["post_datetime"] = pd.NaT

day_recommendation_df["post_datetime"] = pd.to_datetime(
    day_recommendation_df["post_datetime"], format="mixed", errors="coerce"
)
day_recommendation_df = day_recommendation_df.dropna(subset=["post_datetime"]).copy()
if not day_recommendation_df.empty:
    day_recommendation_df["day_of_week"] = day_recommendation_df["post_datetime"].dt.day_name()

day_result = analyze_posting_days(day_recommendation_df) if not day_recommendation_df.empty else pd.DataFrame()
if not day_result.empty:
    day_result = day_result.dropna(subset=["average_engagement_rate", "day_of_week"])

if not day_result.empty:
    best_day = day_result.loc[day_result["average_engagement_rate"].idxmax()]
    day_label = str(best_day["day_of_week"])
    post_count = int(best_day["post_count"])
    average_rate = best_day["average_engagement_rate"]
    median_rate = best_day["median_engagement_rate"]
    std_rate = best_day["engagement_rate_std"]
    st.markdown(f"**Posting day to investigate:** {day_label}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Posts analysed", f"{post_count:,}")
    col2.metric("Average engagement rate", f"{average_rate:.2%}")
    col3.metric("Median engagement rate", f"{median_rate:.2%}")
    if post_count < 10:
        st.warning("Low sample size: treat this as a preliminary insight. Analyse more posts before changing your schedule.")
    else:
        st.info(f"This day-level comparison is based on {post_count:,} posts. A larger sample helps, but does not guarantee that the pattern will continue.")
    if pd.notna(std_rate):
        st.write(f"**Engagement variability:** {std_rate:.2%} (standard deviation).")
    else:
        st.write("**Engagement variability:** Cannot be estimated from a single valid post.")
    st.write(f"**Why investigate this day?** {day_label} had the highest average engagement rate among the posting days in the filtered data.")
    st.write("**Next action:** Test posts on this day against other days using comparable content and topics. Review the results before changing your regular schedule.")
else:
    st.info("Posting-day recommendation is unavailable because valid dates and engagement rates are not available.")

# Best-performing posting hour
hour_recommendation_df = analysis_df.copy()
if "post_datetime" not in hour_recommendation_df.columns:
    hour_recommendation_df["post_datetime"] = pd.NaT
hour_recommendation_df["post_datetime"] = pd.to_datetime(
    hour_recommendation_df["post_datetime"], format="mixed", errors="coerce"
)
hour_recommendation_df = hour_recommendation_df.dropna(subset=["post_datetime"]).copy()
if not hour_recommendation_df.empty:
    hour_recommendation_df["post_hour"] = hour_recommendation_df["post_datetime"].dt.hour

hour_result = analyze_posting_hours(hour_recommendation_df) if not hour_recommendation_df.empty else pd.DataFrame()
if not hour_result.empty:
    hour_result = hour_result.dropna(subset=["average_engagement_rate", "post_hour"])

if not hour_result.empty:
    best_hour = hour_result.loc[hour_result["average_engagement_rate"].idxmax()]
    hour_label = f"{int(best_hour['post_hour']):02d}:00"
    post_count = int(best_hour["post_count"])
    average_rate = best_hour["average_engagement_rate"]
    median_rate = best_hour["median_engagement_rate"]
    std_rate = best_hour["engagement_rate_std"]
    st.markdown(f"**Posting time to investigate:** {hour_label}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Posts analysed", f"{post_count:,}")
    col2.metric("Average engagement rate", f"{average_rate:.2%}")
    col3.metric("Median engagement rate", f"{median_rate:.2%}")
    if post_count < 10:
        st.warning("Low sample size: treat this as a preliminary insight. Analyse more posts before changing your schedule.")
    else:
        st.info(f"This hour-level comparison is based on {post_count:,} posts. The sample size helps with an initial comparison, but does not guarantee future performance.")
    if pd.notna(std_rate):
        st.write(f"**Engagement variability:** {std_rate:.2%} (standard deviation).")
    else:
        st.write("**Engagement variability:** Cannot be estimated from a single valid post.")
    st.write(f"**Why investigate this time?** {hour_label} had the highest average engagement rate among the posting hours in the filtered data.")
    st.write("**Next action:** Test posts at this time against other posting hours using comparable content and topics. Review the results before changing your schedule.")
else:
    st.info("Posting-hour recommendation is unavailable because valid dates and engagement rates are not available.")

st.info(

    "Tip: Compare these results with post counts before changing "

    "your marketing schedule. A high average based on very few posts "

    "may not be reliable."

)







# --------------------------------------------------

# What-if Engagement Planner

# --------------------------------------------------



st.divider()

st.subheader("🎯 What-if Engagement Planner")



st.write(

    "Explore a posting strategy using historical Instagram data. "

    "The result is an estimate based on past posts, not a guarantee."

)



if analysis_df.empty:

    st.warning(

        "The planner is unavailable because no valid posts "

        "remain after metric validation."

    )

else:

    planner_df = analysis_df.copy()



    # Derive day and hour from the actual posting timestamp.

    planner_df["post_datetime"] = pd.to_datetime(

        planner_df["post_datetime"],

        format="mixed",

        errors="coerce",

    )

    planner_df = planner_df.dropna(

        subset=["post_datetime"]

    ).copy()



    planner_df["planner_day"] = (

        planner_df["post_datetime"].dt.day_name()

    )

    planner_df["planner_hour"] = (

        planner_df["post_datetime"].dt.hour

    )



    if planner_df.empty:

        st.warning(

            "The planner needs posts with valid dates "

            "and engagement metrics."

        )

    else:

        day_order = [

            "Monday", "Tuesday", "Wednesday", "Thursday",

            "Friday", "Saturday", "Sunday",

        ]



        col1, col2 = st.columns(2)



        with col1:

            planned_media = st.selectbox(

                "Planned media type",

                options=sorted(

                    planner_df["media_type"].dropna().unique()

                ),

                key="planner_media",

            )



            planned_category = st.selectbox(

                "Planned content category",

                options=sorted(

                    planner_df["content_category"]

                    .dropna()

                    .unique()

                ),

                key="planner_category",

            )



        with col2:

            planned_day = st.selectbox(

                "Planned posting day",

                options=day_order,

                key="planner_day",

            )



            planned_hour = st.selectbox(

                "Planned posting hour",

                options=list(range(24)),

                format_func=lambda hour: f"{hour:02d}:00",

                key="planner_hour",

            )



        planned_impressions = st.number_input(

            "Expected impressions for the planned post",

            min_value=1,

            max_value=100000000,

            value=10000,

            step=1000,

            key="planner_impressions",

        )



        if st.button(

            "Estimate Engagement",

            type="primary",

            key="run_engagement_planner",

        ):

            # Start with posts matching the chosen content strategy.

            matches = planner_df[

                (planner_df["media_type"] == planned_media)

                & (

                    planner_df["content_category"]

                    == planned_category

                )

            ].copy()



            # Prefer matching both day and hour when enough

            # historical posts are available.

            exact_matches = matches[

                (matches["planner_day"] == planned_day)

                & (matches["planner_hour"] == planned_hour)

            ]



            if len(exact_matches) >= 10:

                reference_posts = exact_matches

                comparison_level = (

                    "Matching media type, category, day and hour"

                )

            elif len(matches) >= 10:

                reference_posts = matches

                comparison_level = (

                    "Matching media type and category; "

                    "day/hour sample was too small"

                )

            else:

                media_matches = planner_df[

                    planner_df["media_type"] == planned_media

                ]



                if len(media_matches) >= 10:

                    reference_posts = media_matches

                    comparison_level = (

                        "Matching media type; "

                        "more specific sample was too small"

                    )

                else:

                    reference_posts = planner_df

                    comparison_level = (

                        "All valid historical posts; "

                        "specific samples were too small"

                    )



            historical_median = reference_posts[

                "engagement_rate"

            ].median()



            historical_mean = reference_posts[

                "engagement_rate"

            ].mean()



            estimated_interactions = estimate_interactions(

                planned_impressions,    historical_median

            )



            st.markdown("### Estimated Results")



            result1, result2, result3 = st.columns(3)



            result1.metric(

                "Historical median engagement rate",

                f"{historical_median:.2%}",

            )



            result2.metric(

                "Estimated interactions",

                f"{estimated_interactions:,}",

            )



            result3.metric(

                "Historical reference posts",

                f"{len(reference_posts):,}",

            )



            st.write(

                "**Comparison basis:** " + comparison_level

            )



            st.write(

                f"Historical mean engagement rate: "

                f"{historical_mean:.2%}"

            )



            st.caption(

                "Calculation: planned impressions × historical "

                "median engagement rate. Interactions are estimated "

                "from past data and may differ from actual results. "

                "This is a benchmark calculation, not a trained "

                "machine-learning prediction."

            )
