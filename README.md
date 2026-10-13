# Driving Marketing Success Through Social Media Analytics

## Project Overview

This project is an interactive social media analytics dashboard designed to analyze social media post performance and support data-driven marketing decisions.

Users can upload social media CSV datasets, explore engagement metrics, compare content performance, and identify posting patterns.

## Features

- CSV dataset upload and analysis
- Key performance indicators for likes, comments, shares, saves, reach, and impressions
- Content performance comparison
- Posting day and hour analysis when date information is available
- Data quality validation for missing values, duplicate records, invalid metrics, and engagement-rate issues
- Evidence-based marketing recommendations
- What-if Engagement Planner using historical engagement data
- Hashtag performance analysis when actual hashtag names are available
- Automated tests for key application components

## Technologies Used

- Python
- Pandas
- NumPy
- Streamlit
- Plotly
- Matplotlib
- Pytest

## Project Structure

```text
social_media_analytics/
├── app.py
├── requirements.txt
├── data/
├── modules/
├── tests/
├── .gitignore
└── README.md
```

## Installation and Setup

1. Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

2. Navigate to the project directory:

```bash
cd social_media_analytics
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
streamlit run app.py
```

## How to Use

1. Start the application.
2. Upload a supported social media CSV dataset.
3. Explore engagement metrics and interactive charts.
4. Review data quality results and marketing recommendations.
5. Use the available planning and analysis features.

## Important Notes

Available analyses depend on the columns provided in the uploaded dataset. For example, posting-time analysis requires valid date or time information, and hashtag-level analysis requires actual hashtag names.

The What-if Engagement Planner uses historical engagement benchmarks; it does not guarantee future results.

## Project Status

Developed as a data analytics project to explore social media performance and support informed marketing decisions.

## Author

Add your name and professional profile links here.

## Dataset Attribution

This project uses the Instagram Analytics Dataset published on Kaggle.

- **Dataset:** [Instagram Analytics Dataset](https://www.kaggle.com/datasets/kundanbedmutha/instagram-analytics-dataset)
- **Dataset creator:** Kundan Bedmutha (as listed on Kaggle)
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Modifications:** The dataset is used for social media analytics and dashboard development.

The dataset is credited to its original creator. Please refer to the original Kaggle page for the source dataset and its terms.