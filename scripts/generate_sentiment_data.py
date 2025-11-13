"""
Generate synthetic sentiment training data for NBA teams/players.
In production, this would scrape Twitter, Reddit, news articles, etc.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# NBA teams and star players
TEAMS = [
    "Lakers", "Warriors", "Celtics", "Heat", "Nuggets", "76ers", "Bucks",
    "Suns", "Clippers", "Mavericks", "Knicks", "Nets", "Cavaliers", "Kings",
    "Grizzlies", "Pelicans", "Hawks", "Raptors", "Bulls", "Pacers",
    "Thunder", "Timberwolves", "Magic", "Wizards", "Hornets", "Jazz",
    "Blazers", "Rockets", "Spurs", "Pistons"
]

PLAYERS = [
    "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo",
    "Nikola Jokic", "Luka Doncic", "Joel Embiid", "Jayson Tatum", "Damian Lillard",
    "Anthony Davis", "Kawhi Leonard", "Devin Booker", "Jimmy Butler", "Ja Morant",
    "Trae Young", "Donovan Mitchell", "Zion Williamson", "Paul George",
    "Kyrie Irving", "Bradley Beal", "Jaylen Brown", "De'Aaron Fox", "Anthony Edwards",
    "LaMelo Ball", "Tyrese Haliburton", "Jaren Jackson Jr.", "Paolo Banchero"
]

# Sentiment templates (positive, negative, neutral)
POSITIVE_TEMPLATES = [
    "{entity} is looking amazing this season! Best performance yet.",
    "Absolutely incredible game by {entity} tonight. Clutch!",
    "{entity} is on fire! Championship contender for sure.",
    "What a comeback by {entity}! Never doubted them.",
    "{entity}'s chemistry is unmatched. Pure dominance.",
    "Can't stop watching {entity} play. So entertaining!",
    "{entity} just keeps getting better. Future is bright!",
    "Best player/team in the league right now: {entity}",
    "{entity} proving all the doubters wrong this season.",
    "Historic performance by {entity} tonight. Hall of Fame level."
]

NEGATIVE_TEMPLATES = [
    "{entity} looking terrible tonight. Need major changes.",
    "Disappointing performance from {entity} again. What's going on?",
    "{entity} can't close games. Same issues every year.",
    "Injuries ruining {entity}'s season. So frustrating.",
    "{entity}'s defense is nonexistent. Getting cooked out there.",
    "Trade {entity} already. This isn't working.",
    "{entity} needs to step up or this season is over.",
    "What happened to {entity}? Used to be so good.",
    "{entity} looking lost on both ends. Coaching problems?",
    "Worst game I've seen from {entity} in years."
]

NEUTRAL_TEMPLATES = [
    "{entity} with a solid game tonight. Nothing special.",
    "Average performance by {entity}. On to the next one.",
    "{entity} playing their usual game. Consistent as always.",
    "Close game for {entity} tonight. Could go either way.",
    "{entity} had some good moments and some bad. Mixed bag.",
    "Expected more from {entity} but still a decent showing.",
    "{entity} doing what they need to do. No complaints.",
    "Standard performance from {entity}. Meeting expectations.",
    "{entity} with a quiet game tonight. Flying under radar.",
    "Nothing too exciting from {entity} but getting the job done."
]

def generate_sentiment_data(n_samples: int = 5000) -> pd.DataFrame:
    """Generate synthetic sentiment data"""
    data = []
    
    # Create balanced dataset
    n_per_sentiment = n_samples // 3
    
    for sentiment, templates, score in [
        ('positive', POSITIVE_TEMPLATES, 0.8),
        ('negative', NEGATIVE_TEMPLATES, 0.2),
        ('neutral', NEUTRAL_TEMPLATES, 0.5)
    ]:
        for _ in range(n_per_sentiment):
            # Randomly choose team or player
            is_team = np.random.random() > 0.4
            entity = np.random.choice(TEAMS if is_team else PLAYERS)
            
            # Generate text
            template = np.random.choice(templates)
            text = template.format(entity=entity)
            
            # Add some noise to sentiment scores
            noise = np.random.normal(0, 0.1)
            sentiment_score = np.clip(score + noise, 0, 1)
            
            # Generate timestamp (last 30 days)
            timestamp = datetime.now() - timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24)
            )
            
            data.append({
                'text': text,
                'entity': entity,
                'entity_type': 'team' if is_team else 'player',
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'timestamp': timestamp,
                'source': np.random.choice(['twitter', 'reddit', 'news', 'forum'])
            })
    
    return pd.DataFrame(data)

def main():
    print(f"\n{'='*60}")
    print(f"📊 Generating Sentiment Training Data")
    print(f"{'='*60}\n")
    
    # Generate data
    df = generate_sentiment_data(n_samples=5000)
    
    # Create output directory
    out_dir = Path("artifacts/sentiment")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    out_path = out_dir / "sentiment_training.parquet"
    df.to_parquet(out_path, index=False)
    
    # Print statistics
    print(f"✅ Generated {len(df):,} sentiment samples")
    print(f"\nSentiment Distribution:")
    print(df['sentiment'].value_counts())
    print(f"\nEntity Type Distribution:")
    print(df['entity_type'].value_counts())
    print(f"\nSource Distribution:")
    print(df['source'].value_counts())
    print(f"\nSentiment Score Statistics:")
    print(df.groupby('sentiment')['sentiment_score'].agg(['mean', 'std', 'min', 'max']))
    print(f"\n💾 Saved to: {out_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
