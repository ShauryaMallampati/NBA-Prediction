"""
Generate REAL sentiment data from actual sources:
- Twitter/X API (if available)
- Reddit r/NBA posts and comments
- ESPN/NBA.com headlines
- Basketball-Reference news
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import praw
import requests
from bs4 import BeautifulSoup
import time
import re

# Reddit API (requires credentials in .env)
# Get free API key at: https://www.reddit.com/prefs/apps
def scrape_reddit_sentiment(limit=500):
    """Scrape real sentiment from r/NBA"""
    print("📱 Scraping Reddit r/NBA...")
    
    try:
        # Try to use PRAW if credentials available
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID', 'dummy'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', 'dummy'),
            user_agent='nba_predictor'
        )
        
        posts = []
        subreddit = reddit.subreddit('nba')
        
        for post in subreddit.hot(limit=limit):
            posts.append({
                'text': post.title + ' ' + (post.selftext[:200] if post.selftext else ''),
                'score': post.score,
                'timestamp': datetime.fromtimestamp(post.created_utc),
                'source': 'reddit',
                'url': f"https://reddit.com{post.permalink}"
            })
            
        print(f"  ✅ Scraped {len(posts)} Reddit posts")
        return pd.DataFrame(posts)
        
    except Exception as e:
        print(f"  ⚠️  Reddit API not configured: {e}")
        print("     Get credentials at: https://www.reddit.com/prefs/apps")
        return pd.DataFrame()

def scrape_espn_headlines(pages=5):
    """Scrape ESPN NBA headlines"""
    print("📰 Scraping ESPN headlines...")
    
    articles = []
    try:
        for page in range(1, pages + 1):
            url = f"https://www.espn.com/nba/news"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find headlines
            headlines = soup.find_all('h1', class_='contentItem__title')
            
            for headline in headlines[:20]:  # Top 20 per page
                text = headline.get_text(strip=True)
                if text:
                    articles.append({
                        'text': text,
                        'timestamp': datetime.now() - timedelta(hours=page*12),
                        'source': 'espn',
                        'url': 'espn.com/nba'
                    })
            
            time.sleep(1)  # Rate limit
        
        print(f"  ✅ Scraped {len(articles)} ESPN articles")
        return pd.DataFrame(articles)
        
    except Exception as e:
        print(f"  ⚠️  ESPN scraping failed: {e}")
        return pd.DataFrame()

def scrape_nba_news():
    """Scrape NBA.com news"""
    print("🏀 Scraping NBA.com news...")
    
    articles = []
    try:
        url = "https://www.nba.com/news"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article titles
        titles = soup.find_all(['h1', 'h2', 'h3'], limit=100)
        
        for title in titles:
            text = title.get_text(strip=True)
            if len(text) > 20 and 'NBA' in text.upper():
                articles.append({
                    'text': text,
                    'timestamp': datetime.now(),
                    'source': 'nba.com',
                    'url': 'nba.com/news'
                })
        
        print(f"  ✅ Scraped {len(articles)} NBA.com articles")
        return pd.DataFrame(articles)
        
    except Exception as e:
        print(f"  ⚠️  NBA.com scraping failed: {e}")
        return pd.DataFrame()

def extract_entities(text):
    """Extract team/player names from text"""
    teams = [
        "Lakers", "Warriors", "Celtics", "Heat", "Nuggets", "76ers", "Sixers", 
        "Bucks", "Suns", "Clippers", "Mavericks", "Mavs", "Knicks", "Nets",
        "Cavaliers", "Cavs", "Kings", "Grizzlies", "Pelicans", "Hawks",
        "Raptors", "Bulls", "Pacers", "Thunder", "Timberwolves", "Wolves",
        "Magic", "Wizards", "Hornets", "Jazz", "Blazers", "Rockets", "Spurs", "Pistons"
    ]
    
    players = [
        "LeBron", "Curry", "Durant", "Giannis", "Jokic", "Luka", "Embiid",
        "Tatum", "Lillard", "Davis", "Kawhi", "Booker", "Butler", "Morant",
        "Young", "Mitchell", "Zion", "George", "Irving", "Beal", "Brown",
        "Fox", "Edwards", "Ball", "Haliburton", "Jackson", "Banchero"
    ]
    
    text_upper = text.upper()
    
    for team in teams:
        if team.upper() in text_upper:
            return team, 'team'
    
    for player in players:
        if player.upper() in text_upper:
            return player, 'player'
    
    return None, None

def analyze_sentiment_rule_based(text):
    """Simple rule-based sentiment analysis"""
    text_lower = text.lower()
    
    positive_words = ['amazing', 'incredible', 'great', 'best', 'clutch', 'fire',
                     'dominate', 'win', 'championship', 'elite', 'mvp', 'outstanding',
                     'fantastic', 'excellent', 'impressive', 'unstoppable']
    
    negative_words = ['terrible', 'worst', 'bad', 'disappointing', 'injury', 'loss',
                     'lose', 'struggle', 'awful', 'pathetic', 'trash', 'bust',
                     'overrated', 'weak', 'sad', 'frustrating']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return 'positive', 0.6 + (pos_count * 0.1)
    elif neg_count > pos_count:
        return 'negative', 0.4 - (neg_count * 0.1)
    else:
        return 'neutral', 0.5
    
def main():
    print(f"\n{'='*60}")
    print(f"📊 Generating REAL Sentiment Data")
    print(f"{'='*60}\n")
    
    # Scrape from multiple sources
    dfs = []
    
    # Reddit
    reddit_df = scrape_reddit_sentiment(limit=100)
    if len(reddit_df) > 0:
        dfs.append(reddit_df)
    
    # ESPN
    espn_df = scrape_espn_headlines(pages=3)
    if len(espn_df) > 0:
        dfs.append(espn_df)
    
    # NBA.com
    nba_df = scrape_nba_news()
    if len(nba_df) > 0:
        dfs.append(nba_df)
    
    if len(dfs) == 0:
        print("\n❌ No data scraped from any source!")
        print("   Possible issues:")
        print("   - No Reddit API credentials (get at https://www.reddit.com/prefs/apps)")
        print("   - ESPN/NBA.com blocking requests")
        print("   - Network issues")
        return
    
    # Combine all sources
    all_data = pd.concat(dfs, ignore_index=True)
    
    print(f"\n🔬 Analyzing sentiment...")
    
    # Extract entities and sentiment
    results = []
    for _, row in all_data.iterrows():
        entity, entity_type = extract_entities(row['text'])
        if entity:
            sentiment, score = analyze_sentiment_rule_based(row['text'])
            results.append({
                'text': row['text'],
                'entity': entity,
                'entity_type': entity_type,
                'sentiment': sentiment,
                'sentiment_score': np.clip(score, 0, 1),
                'timestamp': row['timestamp'],
                'source': row['source'],
                'url': row.get('url', '')
            })
    
    sentiment_df = pd.DataFrame(results)
    
    if len(sentiment_df) == 0:
        print("\n⚠️  No entities extracted. Check text parsing logic.")
        return
    
    # Save
    out_dir = Path("artifacts/sentiment")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / "sentiment_real.parquet"
    sentiment_df.to_parquet(out_path, index=False)
    
    # Statistics
    print(f"\n{'='*60}")
    print(f"✅ Scraped {len(sentiment_df):,} REAL sentiment samples")
    print(f"\nSentiment Distribution:")
    print(sentiment_df['sentiment'].value_counts())
    print(f"\nEntity Type Distribution:")
    print(sentiment_df['entity_type'].value_counts())
    print(f"\nSource Distribution:")
    print(sentiment_df['source'].value_counts())
    print(f"\nTop Mentioned Entities:")
    print(sentiment_df['entity'].value_counts().head(10))
    print(f"\n💾 Saved to: {out_path}")
    print(f"{'='*60}\n")
    
    print("\n📝 Sample entries:")
    print(sentiment_df[['text', 'entity', 'sentiment', 'source']].head(5))

if __name__ == "__main__":
    main()
