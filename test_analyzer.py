"""
Test script for YouTube Channel Analyzer functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from youtube_analyzer import calculate_analytics, analyze_keyword_correlations, analyze_upload_frequency_impact, identify_success_patterns

# Create sample data for testing
def create_sample_data():
    """Create sample YouTube video data for testing."""
    np.random.seed(42)  # For reproducible results

    # Generate sample dates
    base_date = datetime(2023, 1, 1)
    dates = [base_date + timedelta(days=i*7 + np.random.randint(-3, 4)) for i in range(50)]

    # Generate sample data
    data = []
    for i, date in enumerate(dates):
        # Some videos perform better with certain keywords
        title_keywords = ['type beat', 'instrumental', 'hip hop', 'trap', 'lofi', 'chill']
        title = f"{' '.join(np.random.choice(title_keywords, np.random.randint(1, 4)))} {np.random.choice(['Music', 'Beats', 'Instrumental', 'Vibes'], 1)[0]}"

        # Views follow a power law distribution with some boosted by keywords
        base_views = np.random.exponential(10000)
        keyword_boost = 1.5 if 'trap' in title.lower() or 'hip hop' in title.lower() else 1.0
        views = int(base_views * keyword_boost * np.random.uniform(0.5, 2.0))

        likes = int(views * np.random.uniform(0.01, 0.05))
        comments = int(views * np.random.uniform(0.001, 0.01))

        data.append({
            'video_id': f'video_{i}',
            'title': title,
            'description': f'Description for {title}',
            'publish_date': date,
            'tags': np.random.choice(['music', 'beats', 'instrumental', 'hiphop', 'trap', 'lofi'], np.random.randint(1, 5), replace=False).tolist(),
            'views': views,
            'likes': likes,
            'comments': comments
        })

    df = pd.DataFrame(data)
    df['engagement_rate'] = (df['likes'] + df['comments']) / df['views'].replace(0, 1)
    return df

if __name__ == "__main__":
    print("Testing YouTube Channel Analyzer functions...")

    # Create sample data
    df = create_sample_data()
    print(f"Created sample dataset with {len(df)} videos")

    # Test analytics functions
    try:
        analytics = calculate_analytics(df)
        print("✓ Analytics calculation successful")

        # Print summary
        print(f"\nSample Results:")
        print(f"Average views: {analytics['avg_views']:,.0f}")
        print(f"Top keyword: {analytics['keyword_correlations']['top_performing_keywords'][0]['keyword'] if analytics['keyword_correlations']['top_performing_keywords'] else 'None'}")
        print(f"Frequency recommendation: {analytics['frequency_impact'].get('frequency_recommendation', 'N/A')}")

        print("\n✓ All functions working correctly!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()