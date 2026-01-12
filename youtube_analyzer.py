"""
YouTube Channel Analyzer for Type Beat Videos

This program analyzes a YouTube channel to understand why some videos succeed.
It collects video data, performs analytics, and generates visualizations.

Requirements:
- Python 3.7+
- Google API key for YouTube Data API v3
- Required packages: google-api-python-client, pandas, matplotlib, seaborn, nltk

Usage:
1. Get a YouTube Data API key from Google Cloud Console
2. Run: python youtube_analyzer.py
3. Enter your API key and channel ID when prompted
"""

import os
import re
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import nltk
from nltk.corpus import stopwords

# Download NLTK stopwords if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def get_channel_uploads_playlist_id(youtube, channel_id):
    """
    Get the uploads playlist ID for a given channel ID.

    Args:
        youtube: YouTube API service object
        channel_id: YouTube channel ID

    Returns:
        str: Uploads playlist ID
    """
    try:
        request = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        else:
            raise ValueError("Channel not found or invalid channel ID")

    except HttpError as e:
        print(f"An error occurred: {e}")
        return None

def get_all_video_ids(youtube, playlist_id):
    """
    Get all video IDs from a playlist.

    Args:
        youtube: YouTube API service object
        playlist_id: Playlist ID

    Returns:
        list: List of video IDs
    """
    video_ids = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def get_video_details(youtube, video_ids):
    """
    Get detailed information for a list of video IDs.

    Args:
        youtube: YouTube API service object
        video_ids: List of video IDs

    Returns:
        list: List of video detail dictionaries
    """
    videos_data = []

    # Process videos in batches of 50 (API limit)
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]

        request = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(batch_ids)
        )
        response = request.execute()

        for item in response['items']:
            snippet = item['snippet']
            statistics = item['statistics']

            video_data = {
                'video_id': item['id'],
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'publish_date': snippet['publishedAt'],
                'tags': snippet.get('tags', []),
                'views': int(statistics.get('viewCount', 0)),
                'likes': int(statistics.get('likeCount', 0)),
                'comments': int(statistics.get('commentCount', 0))
            }

            videos_data.append(video_data)

    return videos_data

def create_dataframe(videos_data):
    """
    Create a pandas DataFrame from video data.

    Args:
        videos_data: List of video dictionaries

    Returns:
        pd.DataFrame: DataFrame with video data
    """
    df = pd.DataFrame(videos_data)

    # Convert publish_date to datetime
    df['publish_date'] = pd.to_datetime(df['publish_date'])

    # Calculate engagement rate
    df['engagement_rate'] = (df['likes'] + df['comments']) / df['views'].replace(0, 1)  # Avoid division by zero

    return df

def save_to_csv(df, filename='youtube_channel_analysis.csv'):
    """
    Save DataFrame to CSV file.

    Args:
        df: pandas DataFrame
        filename: Output filename
    """
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def analyze_keyword_correlations(df):
    """
    Analyze correlations between keywords in titles and view counts.

    Args:
        df: pandas DataFrame

    Returns:
        dict: Keyword correlation analysis
    """
    correlations = {}

    # Get all unique words from titles
    all_title_words = []
    for title in df['title'].str.lower():
        words = re.findall(r'\b\w+\b', title)
        all_title_words.extend(words)

    # Remove stopwords and short words
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in all_title_words if word not in stop_words and len(word) > 2]

    # Count word frequencies
    word_counts = Counter(filtered_words)

    # Analyze correlation for top words
    keyword_stats = []
    for word, count in word_counts.most_common(50):  # Analyze top 50 words
        # Videos containing this word
        videos_with_word = df[df['title'].str.lower().str.contains(r'\b' + re.escape(word) + r'\b', regex=True)]

        if len(videos_with_word) > 0:
            avg_views_with_word = videos_with_word['views'].mean()
            avg_views_without_word = df[~df['title'].str.lower().str.contains(r'\b' + re.escape(word) + r'\b', regex=True)]['views'].mean()

            # Calculate lift (how much better videos with this word perform)
            if avg_views_without_word > 0:
                lift = avg_views_with_word / avg_views_without_word
            else:
                lift = 1.0

            keyword_stats.append({
                'keyword': word,
                'frequency': count,
                'videos_with_keyword': len(videos_with_word),
                'avg_views_with_keyword': avg_views_with_word,
                'avg_views_without_keyword': avg_views_without_word,
                'lift': lift
            })

    # Sort by lift (performance boost)
    keyword_stats.sort(key=lambda x: x['lift'], reverse=True)

    correlations['top_performing_keywords'] = keyword_stats[:20]  # Top 20 by lift
    correlations['correlation_summary'] = f"Found {len(keyword_stats)} keywords with view correlations"

    return correlations

def analyze_upload_frequency_impact(df):
    """
    Analyze how upload frequency affects average views.

    Args:
        df: pandas DataFrame

    Returns:
        dict: Upload frequency impact analysis
    """
    impact = {}

    # Sort by publish date
    df_sorted = df.sort_values('publish_date').copy()

    # Calculate rolling averages to see frequency impact
    if len(df_sorted) >= 10:  # Need minimum videos for analysis
        # Group by month and calculate monthly stats
        df_sorted['month'] = df_sorted['publish_date'].dt.to_period('M')
        monthly_stats = df_sorted.groupby('month').agg({
            'views': ['mean', 'count'],
            'engagement_rate': 'mean'
        }).reset_index()

        monthly_stats.columns = ['month', 'avg_views', 'video_count', 'avg_engagement']

        # Calculate correlation between upload frequency and performance
        if len(monthly_stats) > 1:
            freq_views_corr = monthly_stats['video_count'].corr(monthly_stats['avg_views'])
            freq_engagement_corr = monthly_stats['video_count'].corr(monthly_stats['avg_engagement'])

            impact['frequency_views_correlation'] = freq_views_corr
            impact['frequency_engagement_correlation'] = freq_engagement_corr
            impact['monthly_stats'] = monthly_stats

            # Determine optimal frequency
            if freq_views_corr > 0.3:
                impact['frequency_recommendation'] = "Higher upload frequency correlates with higher views"
            elif freq_views_corr < -0.3:
                impact['frequency_recommendation'] = "Lower upload frequency correlates with higher views"
            else:
                impact['frequency_recommendation'] = "Upload frequency has minimal impact on views"
        else:
            impact['frequency_recommendation'] = "Insufficient data for frequency analysis"
    else:
        impact['frequency_recommendation'] = "Need at least 10 videos for frequency analysis"

    return impact

def identify_success_patterns(df):
    """
    Identify patterns that correlate with successful videos.

    Args:
        df: pandas DataFrame

    Returns:
        dict: Success pattern analysis
    """
    patterns = {}

    # Define success threshold (top 25% of videos by views)
    views_threshold = df['views'].quantile(0.75)
    successful_videos = df[df['views'] >= views_threshold].copy()

    if len(successful_videos) > 0:
        # Title length analysis
        successful_title_lengths = successful_videos['title'].str.len()
        all_title_lengths = df['title'].str.len()

        patterns['avg_title_length_successful'] = successful_title_lengths.mean()
        patterns['avg_title_length_all'] = all_title_lengths.mean()

        # Tag analysis
        successful_tags = []
        for tags in successful_videos['tags']:
            if isinstance(tags, list):
                successful_tags.extend(tags)

        all_tags = []
        for tags in df['tags']:
            if isinstance(tags, list):
                all_tags.extend(tags)

        successful_tag_counts = Counter(successful_tags)
        all_tag_counts = Counter(all_tags)

        # Find tags that appear more frequently in successful videos
        successful_tag_ratios = {}
        for tag, count in successful_tag_counts.items():
            if tag in all_tag_counts:
                ratio = count / all_tag_counts[tag]
                if ratio > 1.5:  # Tags that appear 50% more in successful videos
                    successful_tag_ratios[tag] = ratio

        patterns['successful_tags'] = dict(sorted(successful_tag_ratios.items(), key=lambda x: x[1], reverse=True)[:10])

        # Time-based patterns
        successful_videos['hour'] = successful_videos['publish_date'].dt.hour
        successful_videos['day_of_week'] = successful_videos['publish_date'].dt.day_name()

        patterns['best_upload_hours'] = successful_videos['hour'].value_counts().head(3).to_dict()
        patterns['best_upload_days'] = successful_videos['day_of_week'].value_counts().head(3).to_dict()

    return patterns

def calculate_analytics(df):
    """
    Calculate comprehensive analytics from the video data including correlations and success patterns.

    Args:
        df: pandas DataFrame

    Returns:
        dict: Dictionary with analytics results
    """
    analytics = {}

    # Top 10 most viewed videos
    analytics['top_10_videos'] = df.nlargest(10, 'views')[['title', 'views', 'likes', 'comments']]

    # Average metrics
    analytics['avg_views'] = df['views'].mean()
    analytics['avg_likes'] = df['likes'].mean()
    analytics['avg_comments'] = df['comments'].mean()
    analytics['avg_engagement_rate'] = df['engagement_rate'].mean()

    # Upload frequency
    df_sorted = df.sort_values('publish_date')
    if len(df_sorted) > 1:
        date_range = (df_sorted['publish_date'].max() - df_sorted['publish_date'].min()).days
        if date_range > 0:
            analytics['videos_per_week'] = len(df_sorted) / (date_range / 7)
            analytics['videos_per_month'] = len(df_sorted) / (date_range / 30)
        else:
            analytics['videos_per_week'] = 0
            analytics['videos_per_month'] = 0
    else:
        analytics['videos_per_week'] = 0
        analytics['videos_per_month'] = 0

    # Most common keywords
    all_text = ' '.join(df['title'].tolist() + df['description'].tolist())
    words = re.findall(r'\b\w+\b', all_text.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]

    analytics['common_keywords'] = Counter(filtered_words).most_common(20)

    # NEW: Keyword correlation analysis
    analytics['keyword_correlations'] = analyze_keyword_correlations(df)

    # NEW: Upload frequency impact analysis
    analytics['frequency_impact'] = analyze_upload_frequency_impact(df)

    # NEW: Success patterns
    analytics['success_patterns'] = identify_success_patterns(df)

    return analytics

def print_analytics(analytics):
    """
    Print comprehensive analytics results and success patterns to console.

    Args:
        analytics: Dictionary with analytics results
    """
    print("\n" + "="*60)
    print("YOUTUBE CHANNEL SUCCESS ANALYSIS REPORT")
    print("="*60)

    print("\n📊 BASIC METRICS:")
    print("-" * 30)
    print(f"Average Views: {analytics['avg_views']:,.0f}")
    print(f"Average Likes: {analytics['avg_likes']:,.0f}")
    print(f"Average Comments: {analytics['avg_comments']:,.0f}")
    print(f"Average Engagement Rate: {analytics['avg_engagement_rate']:.4f}")
    print(f"Upload Frequency: {analytics['videos_per_week']:.2f} videos/week")
    print(f"Upload Frequency: {analytics['videos_per_month']:.2f} videos/month")

    print("\n🏆 TOP 10 MOST VIEWED VIDEOS:")
    print("-" * 30)
    print(analytics['top_10_videos'].to_string(index=False))

    print("\n🔍 KEYWORD SUCCESS ANALYSIS:")
    print("-" * 30)
    if 'keyword_correlations' in analytics and analytics['keyword_correlations']['top_performing_keywords']:
        print("Top keywords that boost views (by performance lift):")
        for i, kw in enumerate(analytics['keyword_correlations']['top_performing_keywords'][:10], 1):
            print(f"{i}. '{kw['keyword']}' - {kw['lift']:.2f}x lift, {kw['videos_with_keyword']} videos")
    else:
        print("Insufficient data for keyword correlation analysis")

    print("\n📈 UPLOAD FREQUENCY IMPACT:")
    print("-" * 30)
    freq_impact = analytics.get('frequency_impact', {})
    if 'frequency_recommendation' in freq_impact:
        print(f"Recommendation: {freq_impact['frequency_recommendation']}")
        if 'frequency_views_correlation' in freq_impact:
            corr = freq_impact['frequency_views_correlation']
            print(f"Correlation between upload frequency and views: {corr:.3f}")
            if abs(corr) > 0.3:
                strength = "strong" if abs(corr) > 0.5 else "moderate"
                direction = "positive" if corr > 0 else "negative"
                print(f"This is a {strength} {direction} correlation.")
    else:
        print("Need more videos for frequency impact analysis")

    print("\n🎯 SUCCESS PATTERNS:")
    print("-" * 30)
    patterns = analytics.get('success_patterns', {})
    if patterns:
        if 'avg_title_length_successful' in patterns:
            print(f"Successful videos average title length: {patterns['avg_title_length_successful']:.1f} characters")
            print(f"All videos average title length: {patterns['avg_title_length_all']:.1f} characters")

        if 'successful_tags' in patterns and patterns['successful_tags']:
            print("\nTags that appear more in successful videos:")
            for tag, ratio in list(patterns['successful_tags'].items())[:5]:
                print(f"  '{tag}': {ratio:.1f}x more likely in successful videos")

        if 'best_upload_hours' in patterns:
            print(f"\nBest upload hours: {', '.join(map(str, patterns['best_upload_hours'].keys()))}")

        if 'best_upload_days' in patterns:
            print(f"Best upload days: {', '.join(patterns['best_upload_days'].keys())}")
    else:
        print("Need more videos for pattern analysis")

    print("\n📝 MOST COMMON KEYWORDS (overall):")
    print("-" * 30)
    for keyword, count in analytics['common_keywords'][:15]:
        print(f"{keyword}: {count}")

    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS:")
    print("-" * 30)

    # Generate recommendations based on analysis
    recommendations = []

    # Keyword recommendations
    if 'keyword_correlations' in analytics and analytics['keyword_correlations']['top_performing_keywords']:
        top_kw = analytics['keyword_correlations']['top_performing_keywords'][0]['keyword']
        recommendations.append(f"Include '{top_kw}' in your titles - it shows {analytics['keyword_correlations']['top_performing_keywords'][0]['lift']:.1f}x performance boost")

    # Frequency recommendations
    freq_rec = freq_impact.get('frequency_recommendation', '')
    if 'Higher upload frequency' in freq_rec:
        recommendations.append("Increase your upload frequency - more videos correlate with higher views")
    elif 'Lower upload frequency' in freq_rec:
        recommendations.append("Consider spacing out uploads more - quality over quantity seems to work better")

    # Title length recommendations
    if 'avg_title_length_successful' in patterns and 'avg_title_length_all' in patterns:
        success_len = patterns['avg_title_length_successful']
        all_len = patterns['avg_title_length_all']
        if success_len > all_len * 1.1:
            recommendations.append(f"Make titles longer (aim for {success_len:.0f} characters) - successful videos have longer titles")
        elif success_len < all_len * 0.9:
            recommendations.append(f"Make titles shorter (aim for {success_len:.0f} characters) - successful videos have shorter titles")

    if not recommendations:
        recommendations.append("Keep doing what works - your channel shows consistent performance")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    print("\n" + "="*60)

def create_visualizations(df, output_dir='visualizations'):
    """
    Create and save comprehensive visualizations for success pattern analysis.

    Args:
        df: pandas DataFrame
        output_dir: Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set style
    sns.set_style("whitegrid")

    # 1. Views distribution histogram
    plt.figure(figsize=(12, 8))
    plt.hist(df['views'], bins=50, edgecolor='black', alpha=0.7, color='skyblue')
    plt.title('Distribution of Video Views', fontsize=16, fontweight='bold')
    plt.xlabel('Views', fontsize=12)
    plt.ylabel('Number of Videos', fontsize=12)
    plt.yscale('log')
    plt.axvline(df['views'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["views"].mean():,.0f}')
    plt.axvline(df['views'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df["views"].median():,.0f}')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'views_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Engagement vs Views scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(df['views'], df['engagement_rate'], alpha=0.6, s=60, c=df['views'], cmap='viridis')
    plt.colorbar(scatter, label='Views')
    plt.title('Engagement Rate vs Views', fontsize=16, fontweight='bold')
    plt.xlabel('Views', fontsize=12)
    plt.ylabel('Engagement Rate', fontsize=12)
    plt.xscale('log')

    # Add trend line
    if len(df) > 1:
        z = np.polyfit(np.log(df['views'] + 1), df['engagement_rate'], 1)
        p = np.poly1d(z)
        x_trend = np.logspace(np.log10(df['views'].min() + 1), np.log10(df['views'].max() + 1), 100)
        plt.plot(x_trend, p(np.log(x_trend)), "r--", alpha=0.8, linewidth=2, label='Trend line')

    plt.legend()
    plt.savefig(os.path.join(output_dir, 'engagement_vs_views.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Time series plot showing views over time
    df_timeline = df.sort_values('publish_date').copy()
    df_timeline['cumulative_videos'] = range(1, len(df_timeline) + 1)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Top plot: Views over time
    ax1.scatter(df_timeline['publish_date'], df_timeline['views'], alpha=0.7, s=50, color='blue')
    ax1.plot(df_timeline['publish_date'], df_timeline['views'].rolling(window=5, min_periods=1).mean(),
             color='red', linewidth=2, label='5-video rolling average')
    ax1.set_title('Video Views Over Time', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Views', fontsize=12)
    ax1.set_yscale('log')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Cumulative uploads
    ax2.plot(df_timeline['publish_date'], df_timeline['cumulative_videos'],
             marker='o', linestyle='-', linewidth=2, color='green', markersize=4)
    ax2.fill_between(df_timeline['publish_date'], df_timeline['cumulative_videos'], alpha=0.3, color='green')
    ax2.set_title('Cumulative Video Uploads Over Time', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Upload Date', fontsize=12)
    ax2.set_ylabel('Total Videos', fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'views_timeline.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Additional visualization: Title length vs views
    plt.figure(figsize=(12, 8))
    title_lengths = df['title'].str.len()
    plt.scatter(title_lengths, df['views'], alpha=0.6, s=50, color='purple')
    plt.title('Video Views vs Title Length', fontsize=16, fontweight='bold')
    plt.xlabel('Title Length (characters)', fontsize=12)
    plt.ylabel('Views', fontsize=12)
    plt.yscale('log')

    # Add correlation line
    if len(df) > 1:
        corr_coef = title_lengths.corr(df['views'])
        plt.text(0.05, 0.95, f'Correlation: {corr_coef:.3f}',
                transform=plt.gca().transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.savefig(os.path.join(output_dir, 'title_length_vs_views.png'), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Enhanced visualizations saved to {output_dir}/ directory")

def main():
    """
    Main function to run the YouTube channel analyzer.
    """
    print("YouTube Channel Analyzer for Type Beat Videos")
    print("=" * 50)

    # Get API key and channel ID from user
    api_key = input("Enter your YouTube Data API v3 key: ").strip()
    channel_id = input("Enter the YouTube channel ID: ").strip()

    # Build YouTube API service
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        # Get uploads playlist ID
        print("Fetching channel information...")
        playlist_id = get_channel_uploads_playlist_id(youtube, channel_id)
        if not playlist_id:
            print("Failed to get playlist ID. Please check your channel ID.")
            return

        # Get all video IDs
        print("Fetching video list...")
        video_ids = get_all_video_ids(youtube, playlist_id)
        print(f"Found {len(video_ids)} videos")

        if not video_ids:
            print("No videos found in this channel.")
            return

        # Get video details
        print("Fetching video details...")
        videos_data = get_video_details(youtube, video_ids)

        # Create DataFrame
        df = create_dataframe(videos_data)

        # Save to CSV
        save_to_csv(df)

        # Calculate analytics
        analytics = calculate_analytics(df)

        # Print analytics
        print_analytics(analytics)

        # Create visualizations
        create_visualizations(df)

        print("\nAnalysis complete! Check the CSV file and visualizations folder.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()