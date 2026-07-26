# goal-action-tracker


# Goal & Action Tracker

A Streamlit-based web application designed to track and categorize daily time expenditure across distinct activity streams. The app uses SQLite for persistent storage and displays real-time metrics along with historical analytics.

## Features

- **Activity Tracking**: Real-time timer to track active sessions across customizable categories.
- **Background Persistence**: Timestamp-based tracking stored in SQLite so timing continues uninterrupted when browser tabs are closed or backgrounded on mobile.
- **Standard Formatting**: Formats total elapsed time strictly in `DD:HH:MM:SS` (Days:Hours:Minutes:Seconds).
- **Time Range Filtering**: View metrics broken down by Today, Last 7 Days, or All Time.
- **Daily Analytics**: Aggregated day-by-day summaries and interactive stacked bar charts.

## Technologies Used

- **Python 3.10+**
- **Streamlit** (UI Framework)
- **Pandas** (Data Manipulation)
- **SQLite3** (Database)

## Project Structure

```text
├── app.py              # Main application script
├── tracker.db          # SQLite database (created automatically)
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
