# YouTube Channel Analyzer for Type Beat Videos

This Python program analyzes YouTube channels focused on type beats to understand what makes videos successful. It collects comprehensive data about videos, performs analytics, and generates visualizations.

## Features

- **Data Collection**: Gathers detailed information about all videos in a channel
- **Success Pattern Analysis**: Identifies what makes videos successful
- **Correlation Analysis**: Analyzes keyword performance and upload frequency impact
- **Advanced Analytics**: Calculates engagement rates, view distributions, and performance patterns
- **Comprehensive Visualizations**: Creates multiple charts showing success patterns and trends
- **Data Export**: Saves all data to CSV for further analysis
- **Actionable Recommendations**: Provides specific suggestions for improving video performance

## Setup Instructions

### 1. Prerequisites

- Python 3.7 or higher
- Google Cloud account with YouTube Data API enabled

### 2. Get YouTube Data API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key (you'll need it when running the program)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the automated setup script:

```bash
python setup_and_run.py
```

On Windows, you can also double-click `run_analyzer.bat` to run the setup and program.

### 4. Run the Program

```bash
python youtube_analyzer.py
```

When prompted:

- Enter your YouTube Data API v3 key
- Enter the channel ID you want to analyze

You can find a channel ID by:

- Going to the channel's YouTube page
- Right-clicking and selecting "View page source"
- Searching for "channelId" in the HTML

### 5. Test the Functions (Optional)

```bash
python test_analyzer.py
```

This runs the analysis functions on sample data to verify everything works correctly.

## Output

The program will generate:

1. **CSV File**: `youtube_channel_analysis.csv` with all video data including calculated engagement rates
2. **Console Report**: Comprehensive success analysis report with:
   - Basic metrics and top performing videos
   - Keyword correlation analysis showing which words boost views
   - Upload frequency impact assessment
   - Success patterns (title length, tags, optimal upload times)
   - Specific recommendations for improving performance
3. **Enhanced Visualizations**: Four detailed charts saved in the `visualizations/` folder:
   - Views distribution histogram with mean/median lines
   - Engagement rate vs views scatter plot with trend line
   - Time series showing views growth over time (dual plot)
   - Title length vs views correlation analysis

## Data Collected

For each video:

- Video ID
- Title
- Description
- Publish date
- View count
- Like count
- Comment count
- Tags
- Engagement rate (calculated)

## Analytics Performed

- **Engagement Rate**: (likes + comments) / views for each video
- **Top 10 Most Viewed Videos**: Performance leaderboard
- **Average Metrics**: Views, likes, comments, and engagement rates
- **Upload Frequency**: Videos per week/month calculation
- **Keyword Correlation Analysis**: Which title keywords correlate with higher views
- **Upload Frequency Impact**: How posting frequency affects average performance
- **Success Patterns**: Title length, tags, and optimal upload timing analysis
- **Performance Lift Calculation**: How much certain keywords boost view counts

## Troubleshooting

- **Quota exceeded**: YouTube API has daily limits. If you hit the limit, wait until the quota resets or upgrade your API plan.
- **Channel not found**: Double-check the channel ID. Make sure it's the correct format (starts with UC...).
- **Import errors**: Make sure all dependencies are installed correctly.

## Notes

- The program may take some time to run for channels with many videos
- NLTK will download stopwords on first run if not already available
- All visualizations are saved as PNG files with high resolution
