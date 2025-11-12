"""
Sports Betting Odds Scraper
Fetches odds from multiple sportsbooks (DraftKings, FanDuel, BetMGM)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, List, Optional
import re

class OddsScraper:
    """Scraper for sports betting odds"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self) -> Dict[str, str]:
        """Map team names to abbreviations"""
        return {
            'atlanta hawks': 'ATL', 'hawks': 'ATL',
            'boston celtics': 'BOS', 'celtics': 'BOS',
            'brooklyn nets': 'BKN', 'nets': 'BKN',
            'charlotte hornets': 'CHA', 'hornets': 'CHA',
            'chicago bulls': 'CHI', 'bulls': 'CHI',
            'cleveland cavaliers': 'CLE', 'cavaliers': 'CLE',
            'dallas mavericks': 'DAL', 'mavericks': 'DAL',
            'denver nuggets': 'DEN', 'nuggets': 'DEN',
            'detroit pistons': 'DET', 'pistons': 'DET',
            'golden state warriors': 'GSW', 'warriors': 'GSW',
            'houston rockets': 'HOU', 'rockets': 'HOU',
            'indiana pacers': 'IND', 'pacers': 'IND',
            'la clippers': 'LAC', 'clippers': 'LAC',
            'los angeles lakers': 'LAL', 'lakers': 'LAL',
            'memphis grizzlies': 'MEM', 'grizzlies': 'MEM',
            'miami heat': 'MIA', 'heat': 'MIA',
            'milwaukee bucks': 'MIL', 'bucks': 'MIL',
            'minnesota timberwolves': 'MIN', 'timberwolves': 'MIN',
            'new orleans pelicans': 'NOP', 'pelicans': 'NOP',
            'new york knicks': 'NYK', 'knicks': 'NYK',
            'oklahoma city thunder': 'OKC', 'thunder': 'OKC',
            'orlando magic': 'ORL', 'magic': 'ORL',
            'philadelphia 76ers': 'PHI', '76ers': 'PHI', 'sixers': 'PHI',
            'phoenix suns': 'PHX', 'suns': 'PHX',
            'portland trail blazers': 'POR', 'blazers': 'POR',
            'sacramento kings': 'SAC', 'kings': 'SAC',
            'san antonio spurs': 'SAS', 'spurs': 'SAS',
            'toronto raptors': 'TOR', 'raptors': 'TOR',
            'utah jazz': 'UTA', 'jazz': 'UTA',
            'washington wizards': 'WAS', 'wizards': 'WAS',
        }
    
    def american_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
    
    def parse_team_name(self, raw_name: str) -> Optional[str]:
        """Parse team name from raw text"""
        raw_lower = raw_name.lower().strip()
        
        # Direct match
        if raw_lower in self.team_mapping:
            return self.team_mapping[raw_lower]
        
        # Partial match
        for key, abbr in self.team_mapping.items():
            if key in raw_lower or raw_lower in key:
                return abbr
        
        return None
    
    def scrape_odds_api(self) -> pd.DataFrame:
        """
        Scrape odds using The Odds API (requires API key)
        Free tier: 500 requests/month
        Sign up at: https://the-odds-api.com/
        """
        
        # NOTE: You need to sign up for a free API key
        # Set your key in environment variable: ODDS_API_KEY
        import os
        api_key = os.getenv('ODDS_API_KEY', '')
        
        if not api_key:
            print("⚠️  No ODDS_API_KEY found in environment")
            print("   Sign up at https://the-odds-api.com/ for a free key")
            print("   Then: export ODDS_API_KEY='your-key-here'")
            return pd.DataFrame()
        
        print("\n💰 Fetching odds from The Odds API...")
        
        try:
            url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
            params = {
                'apiKey': api_key,
                'regions': 'us',  # US bookmakers
                'markets': 'h2h',  # Head-to-head (moneyline)
                'oddsFormat': 'american',
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            odds_list = []
            
            for game in data:
                home_team_raw = game.get('home_team', '')
                away_team_raw = game.get('away_team', '')
                commence_time = game.get('commence_time', '')
                
                home_team = self.parse_team_name(home_team_raw)
                away_team = self.parse_team_name(away_team_raw)
                
                if not home_team or not away_team:
                    print(f"   ⚠️  Could not parse: {away_team_raw} @ {home_team_raw}")
                    continue
                
                # Get odds from each bookmaker
                bookmakers = game.get('bookmakers', [])
                
                for book in bookmakers:
                    book_name = book.get('key', '')
                    markets = book.get('markets', [])
                    
                    for market in markets:
                        if market.get('key') == 'h2h':
                            outcomes = market.get('outcomes', [])
                            
                            home_odds = None
                            away_odds = None
                            
                            for outcome in outcomes:
                                team_name = outcome.get('name', '')
                                odds = outcome.get('price', 0)
                                
                                if team_name == home_team_raw:
                                    home_odds = odds
                                elif team_name == away_team_raw:
                                    away_odds = odds
                            
                            if home_odds and away_odds:
                                odds_list.append({
                                    'game_time': commence_time,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'sportsbook': book_name,
                                    'home_odds': home_odds,
                                    'away_odds': away_odds,
                                    'home_implied_prob': self.american_to_probability(home_odds),
                                    'away_implied_prob': self.american_to_probability(away_odds),
                                    'scraped_at': datetime.now().isoformat()
                                })
            
            df = pd.DataFrame(odds_list)
            print(f"✅ Fetched odds for {len(df) // 3 if len(df) > 0 else 0} games from {len(df)} bookmakers")
            
            # Show remaining requests
            remaining = response.headers.get('x-requests-remaining', 'unknown')
            print(f"   Remaining API requests: {remaining}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching odds: {e}")
            return pd.DataFrame()
    
    def calculate_betting_edges(self, predictions_df: pd.DataFrame, odds_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate betting edges by comparing model predictions to market odds
        
        Betting edge = Model probability - Market implied probability
        Positive edge = value bet (model thinks team is undervalued)
        """
        
        print("\n🎯 Calculating betting edges...")
        
        if predictions_df.empty or odds_df.empty:
            print("❌ Missing predictions or odds data")
            return pd.DataFrame()
        
        edges = []
        
        for _, pred in predictions_df.iterrows():
            game_id = pred.get('game_id', '')
            home_team = pred['home_team']
            away_team = pred['away_team']
            home_model_prob = pred['home_win_prob']
            away_model_prob = pred['away_win_prob']
            
            # Find odds for this game
            game_odds = odds_df[
                (odds_df['home_team'] == home_team) & 
                (odds_df['away_team'] == away_team)
            ]
            
            if game_odds.empty:
                continue
            
            # Average odds across all bookmakers
            avg_home_implied = game_odds['home_implied_prob'].mean()
            avg_away_implied = game_odds['away_implied_prob'].mean()
            
            # Calculate edges
            home_edge = home_model_prob - avg_home_implied
            away_edge = away_model_prob - avg_away_implied
            
            # Get best odds
            best_home_odds = game_odds.loc[game_odds['home_odds'].idxmax()]['home_odds']
            best_away_odds = game_odds.loc[game_odds['away_odds'].idxmax()]['away_odds']
            best_home_book = game_odds.loc[game_odds['home_odds'].idxmax()]['sportsbook']
            best_away_book = game_odds.loc[game_odds['away_odds'].idxmax()]['sportsbook']
            
            # Determine recommended bet (only if edge > 5%)
            recommended_bet = None
            bet_size = None
            expected_value = None
            
            if home_edge > 0.05:  # 5% edge threshold
                recommended_bet = 'home'
                bet_size = min(home_edge * 10, 5)  # Kelly Criterion simplified (max 5% of bankroll)
                expected_value = home_model_prob * best_home_odds - (1 - home_model_prob)
            elif away_edge > 0.05:
                recommended_bet = 'away'
                bet_size = min(away_edge * 10, 5)
                expected_value = away_model_prob * best_away_odds - (1 - away_model_prob)
            
            edges.append({
                'game_id': game_id,
                'home_team': home_team,
                'away_team': away_team,
                'home_model_prob': home_model_prob,
                'away_model_prob': away_model_prob,
                'home_market_prob': avg_home_implied,
                'away_market_prob': avg_away_implied,
                'home_edge': home_edge,
                'away_edge': away_edge,
                'best_home_odds': best_home_odds,
                'best_away_odds': best_away_odds,
                'best_home_book': best_home_book,
                'best_away_book': best_away_book,
                'recommended_bet': recommended_bet,
                'bet_size_pct': bet_size,
                'expected_value': expected_value,
                'calculated_at': datetime.now().isoformat()
            })
        
        edges_df = pd.DataFrame(edges)
        
        # Show value bets
        value_bets = edges_df[edges_df['recommended_bet'].notna()]
        if not value_bets.empty:
            print(f"✅ Found {len(value_bets)} value bets!")
            for _, bet in value_bets.iterrows():
                team = bet['home_team'] if bet['recommended_bet'] == 'home' else bet['away_team']
                edge = bet['home_edge'] if bet['recommended_bet'] == 'home' else bet['away_edge']
                odds = bet['best_home_odds'] if bet['recommended_bet'] == 'home' else bet['best_away_odds']
                book = bet['best_home_book'] if bet['recommended_bet'] == 'home' else bet['best_away_book']
                
                print(f"   💎 BET {team}: {edge*100:.1f}% edge, odds {odds:+d} @ {book}")
                print(f"      Recommended bet: {bet['bet_size_pct']:.1f}% of bankroll, EV: {bet['expected_value']:.3f}")
        else:
            print("   No value bets found (all edges < 5%)")
        
        return edges_df
    
    def save_odds_and_edges(self, output_dir: str = "data/odds"):
        """Scrape odds and calculate edges"""
        
        print("\n" + "="*80)
        print("BETTING ODDS & EDGE CALCULATION")
        print("="*80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Scrape odds
        odds_df = self.scrape_odds_api()
        
        if not odds_df.empty:
            odds_path = output_path / f"odds_{today}.csv"
            odds_df.to_csv(odds_path, index=False)
            print(f"\n✅ Saved odds to {odds_path}")
            
            # Load predictions
            predictions_path = Path(f"artifacts/predictions/predictions_{today}.csv")
            if predictions_path.exists():
                predictions_df = pd.read_csv(predictions_path)
                
                # Calculate edges
                edges_df = self.calculate_betting_edges(predictions_df, odds_df)
                
                if not edges_df.empty:
                    edges_path = output_path / f"betting_edges_{today}.csv"
                    edges_df.to_csv(edges_path, index=False)
                    print(f"✅ Saved betting edges to {edges_path}")
            else:
                print(f"⚠️  No predictions found for {today}")
                print("   Run: poetry run python scripts/generate_todays_predictions.py")
        
        print("\n" + "="*80)
        print("✅ ODDS SCRAPING COMPLETE!")
        print("="*80)
        
        return odds_df


if __name__ == "__main__":
    scraper = OddsScraper()
    scraper.save_odds_and_edges()
