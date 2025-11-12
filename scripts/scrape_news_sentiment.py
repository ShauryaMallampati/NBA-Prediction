"""
NBA News & Sentiment Analysis Scraper
Scrapes and analyzes:
- ESPN team news
- NBA.com headlines
- Recent controversies/injuries
- Sentiment scoring (positive/negative/neutral)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
import re
from typing import Dict, List, Tuple
from textblob import TextBlob
import json

class NewsSentimentScraper:
    """Scraper for NBA news and sentiment analysis"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self) -> Dict:
        """Map team abbreviations to full names"""
        return {
            'ATL': 'Atlanta Hawks',
            'BOS': 'Boston Celtics',
            'BKN': 'Brooklyn Nets',
            'CHA': 'Charlotte Hornets',
            'CHI': 'Chicago Bulls',
            'CLE': 'Cleveland Cavaliers',
            'DAL': 'Dallas Mavericks',
            'DEN': 'Denver Nuggets',
            'DET': 'Detroit Pistons',
            'GSW': 'Golden State Warriors',
            'HOU': 'Houston Rockets',
            'IND': 'Indiana Pacers',
            'LAC': 'LA Clippers',
            'LAL': 'Los Angeles Lakers',
            'MEM': 'Memphis Grizzlies',
            'MIA': 'Miami Heat',
            'MIL': 'Milwaukee Bucks',
            'MIN': 'Minnesota Timberwolves',
            'NOP': 'New Orleans Pelicans',
            'NYK': 'New York Knicks',
            'OKC': 'Oklahoma City Thunder',
            'ORL': 'Orlando Magic',
            'PHI': 'Philadelphia 76ers',
            'PHX': 'Phoenix Suns',
            'POR': 'Portland Trail Blazers',
            'SAC': 'Sacramento Kings',
            'SAS': 'San Antonio Spurs',
            'TOR': 'Toronto Raptors',
            'UTA': 'Utah Jazz',
            'WAS': 'Washington Wizards',
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of text using TextBlob
        Returns: (sentiment_label, sentiment_score)
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            return label, polarity
            
        except Exception as e:
            print(f"⚠️  Sentiment analysis error: {e}")
            return 'neutral', 0.0
    
    def scrape_espn_team_news(self, team_abbr: str) -> List[Dict]:
        """Scrape ESPN news for a specific team"""
        team_name = self.team_mapping.get(team_abbr, '')
        
        if not team_name:
            return []
        
        # ESPN team page
        team_slug = team_name.lower().replace(' ', '-')
        url = f"https://www.espn.com/nba/team/_/name/{team_abbr.lower()}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            
            # Find news sections
            news_sections = soup.find_all('section', class_=re.compile('.*News.*|.*Article.*'))
            
            for section in news_sections[:5]:  # Top 5 news items
                headlines = section.find_all(['h1', 'h2', 'h3', 'a'])
                
                for headline in headlines[:3]:
                    text = headline.get_text(strip=True)
                    
                    if text and len(text) > 20:  # Filter out short snippets
                        sentiment_label, sentiment_score = self.analyze_sentiment(text)
                        
                        news_items.append({
                            'team': team_abbr,
                            'headline': text,
                            'sentiment': sentiment_label,
                            'sentiment_score': sentiment_score,
                            'source': 'ESPN',
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
            
            return news_items
            
        except Exception as e:
            print(f"⚠️  Error scraping ESPN news for {team_abbr}: {e}")
            return []
    
    def scrape_nba_com_news(self, team_abbr: str) -> List[Dict]:
        """Scrape NBA.com news for a specific team"""
        team_name = self.team_mapping.get(team_abbr, '')
        
        if not team_name:
            return []
        
        try:
            # NBA.com news API
            url = "https://www.nba.com/news"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            
            # Find articles mentioning the team
            articles = soup.find_all('article', limit=20)
            
            for article in articles:
                headline_elem = article.find(['h1', 'h2', 'h3', 'a'])
                
                if headline_elem:
                    text = headline_elem.get_text(strip=True)
                    
                    # Check if team is mentioned
                    if team_name.lower() in text.lower() or team_abbr.lower() in text.lower():
                        sentiment_label, sentiment_score = self.analyze_sentiment(text)
                        
                        news_items.append({
                            'team': team_abbr,
                            'headline': text,
                            'sentiment': sentiment_label,
                            'sentiment_score': sentiment_score,
                            'source': 'NBA.com',
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
            
            return news_items
            
        except Exception as e:
            print(f"⚠️  Error scraping NBA.com news for {team_abbr}: {e}")
            return []
    
    def detect_controversy_keywords(self, text: str) -> bool:
        """Detect controversy/negative keywords"""
        controversy_keywords = [
            'suspended', 'fined', 'injured', 'out', 'ruled out',
            'investigation', 'controversy', 'conflict', 'dispute',
            'ejected', 'technical foul', 'flagrant', 'fight',
            'trade rumors', 'unhappy', 'disappointed', 'frustrated',
            'benched', 'DNP', 'questionable', 'doubtful'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in controversy_keywords)
    
    def scrape_all_team_news(self) -> pd.DataFrame:
        """Scrape news for all teams"""
        print("\n📰 Scraping News for All Teams...")
        print("="*80)
        
        all_news = []
        
        for team_abbr in self.team_mapping.keys():
            print(f"\n🔍 Scraping news for {team_abbr}...")
            
            # ESPN news
            espn_news = self.scrape_espn_team_news(team_abbr)
            all_news.extend(espn_news)
            
            time.sleep(1)  # Rate limiting
            
            # NBA.com news
            nba_news = self.scrape_nba_com_news(team_abbr)
            all_news.extend(nba_news)
            
            time.sleep(1)
            
            print(f"   Found {len(espn_news) + len(nba_news)} articles")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_news)
        
        if not df.empty:
            # Add controversy flag
            df['has_controversy'] = df['headline'].apply(self.detect_controversy_keywords)
            
            print(f"\n✅ Total articles scraped: {len(df)}")
            print(f"   Positive: {len(df[df['sentiment'] == 'positive'])}")
            print(f"   Negative: {len(df[df['sentiment'] == 'negative'])}")
            print(f"   Neutral: {len(df[df['sentiment'] == 'neutral'])}")
            print(f"   Controversies detected: {df['has_controversy'].sum()}")
        
        return df
    
    def aggregate_team_sentiment(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate news sentiment by team"""
        print("\n📊 Aggregating sentiment by team...")
        
        if news_df.empty:
            return pd.DataFrame()
        
        # Group by team
        team_sentiment = news_df.groupby('team').agg({
            'sentiment_score': ['mean', 'std', 'min', 'max'],
            'has_controversy': 'sum',
            'headline': 'count'
        }).reset_index()
        
        # Flatten column names
        team_sentiment.columns = [
            'TEAM_ABBR',
            'news_sentiment_avg',
            'news_sentiment_std',
            'news_sentiment_min',
            'news_sentiment_max',
            'news_controversy_count',
            'news_article_count'
        ]
        
        # Calculate sentiment category distribution
        sentiment_dist = news_df.groupby(['team', 'sentiment']).size().unstack(fill_value=0)
        sentiment_dist.columns = [f'news_{col}_count' for col in sentiment_dist.columns]
        sentiment_dist.reset_index(inplace=True)
        sentiment_dist.rename(columns={'team': 'TEAM_ABBR'}, inplace=True)
        
        # Merge
        team_sentiment = team_sentiment.merge(sentiment_dist, on='TEAM_ABBR', how='left')
        
        # Calculate sentiment momentum (recent trend)
        recent_sentiment = news_df.sort_values('date', ascending=False).groupby('team').head(3)
        recent_avg = recent_sentiment.groupby('team')['sentiment_score'].mean().reset_index()
        recent_avg.columns = ['TEAM_ABBR', 'news_sentiment_recent']
        
        team_sentiment = team_sentiment.merge(recent_avg, on='TEAM_ABBR', how='left')
        
        print(f"✅ Sentiment aggregated for {len(team_sentiment)} teams")
        
        return team_sentiment
    
    def save_news_data(self, output_dir: str = "data/news"):
        """Scrape and save news data"""
        
        print("\n" + "="*80)
        print("NBA NEWS & SENTIMENT SCRAPER")
        print("="*80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Scrape all news
        news_df = self.scrape_all_team_news()
        
        if not news_df.empty:
            # Save raw news
            raw_path = output_path / f"raw_news_{today}.csv"
            news_df.to_csv(raw_path, index=False)
            print(f"\n✅ Saved raw news: {raw_path}")
            
            # Aggregate by team
            team_sentiment = self.aggregate_team_sentiment(news_df)
            
            if not team_sentiment.empty:
                agg_path = output_path / f"team_sentiment_{today}.csv"
                team_sentiment.to_csv(agg_path, index=False)
                print(f"✅ Saved team sentiment: {agg_path}")
                
                # Save as JSON for API
                json_path = output_path / f"team_sentiment_{today}.json"
                team_sentiment.to_json(json_path, orient='records', indent=2)
                print(f"✅ Saved JSON: {json_path}")
        
        print("\n" + "="*80)
        print("✅ NEWS SCRAPING COMPLETE!")
        print("="*80)
        
        return news_df, team_sentiment


if __name__ == "__main__":
    scraper = NewsSentimentScraper()
    news_df, sentiment_df = scraper.save_news_data()
    
    if not sentiment_df.empty:
        print("\n📊 Top 5 Most Positive Teams:")
        print(sentiment_df.nlargest(5, 'news_sentiment_avg')[['TEAM_ABBR', 'news_sentiment_avg']])
        
        print("\n📊 Top 5 Most Negative Teams:")
        print(sentiment_df.nsmallest(5, 'news_sentiment_avg')[['TEAM_ABBR', 'news_sentiment_avg']])
        
        print("\n📊 Teams with Most Controversies:")
        print(sentiment_df.nlargest(5, 'news_controversy_count')[['TEAM_ABBR', 'news_controversy_count']])
