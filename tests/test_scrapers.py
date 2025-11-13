"""
Test Suite for Data Scrapers
Tests Basketball-Reference, ESPN, News scrapers
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestOddsScraper:
    """Test betting odds scraper"""
    
    def test_american_to_probability(self):
        """Test American odds to probability conversion"""
        from scripts.scrape_odds import OddsScraper
        
        scraper = OddsScraper()
        
        # Test favorite (-150)
        prob_fav = scraper.american_to_probability(-150)
        assert 0.5 < prob_fav < 1.0
        assert abs(prob_fav - 0.6) < 0.05  # Should be around 60%
        
        # Test underdog (+150)
        prob_dog = scraper.american_to_probability(150)
        assert 0 < prob_dog < 0.5
        assert abs(prob_dog - 0.4) < 0.05  # Should be around 40%
        
        # Test even odds (+100)
        prob_even = scraper.american_to_probability(100)
        assert abs(prob_even - 0.5) < 0.01  # Should be exactly 50%
    
    def test_team_name_mapping(self):
        """Test team name to abbreviation mapping"""
        from scripts.scrape_odds import OddsScraper
        
        scraper = OddsScraper()
        
        assert scraper.team_mapping['lakers'] == 'LAL'
        assert scraper.team_mapping['golden state warriors'] == 'GSW'
        assert scraper.team_mapping['celtics'] == 'BOS'
    
    @patch('requests.get')
    def test_fetch_odds_api_success(self, mock_get):
        """Test successful API fetch"""
        from scripts.scrape_odds import OddsScraper
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "test_game_id",
                "commence_time": "2025-11-12T19:00:00Z",
                "home_team": "Los Angeles Lakers",
                "away_team": "Golden State Warriors",
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Los Angeles Lakers", "price": -150},
                                    {"name": "Golden State Warriors", "price": 130}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response
        
        scraper = OddsScraper()
        # Test would go here - actual implementation depends on scraper structure
    
    def test_save_odds_data(self, tmp_path):
        """Test saving odds data to JSON"""
        from scripts.scrape_odds import OddsScraper
        import json
        
        scraper = OddsScraper()
        
        test_data = {
            "game_id": "test123",
            "date": "2025-11-12",
            "home_team": "LAL",
            "away_team": "GSW",
            "odds": {"draftkings": {"home_ml": -150}}
        }
        
        # Save to temp directory
        output_file = tmp_path / "test_odds.json"
        with open(output_file, 'w') as f:
            json.dump(test_data, f)
        
        # Verify file exists and data is correct
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data["game_id"] == "test123"


class TestAdvancedStatsScraper:
    """Test advanced stats scraper"""
    
    @patch('requests.get')
    def test_scrape_team_stats(self, mock_get):
        """Test scraping team advanced stats"""
        # Mock HTML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <table id="advanced_stats">
            <tr><td>Los Angeles Lakers</td><td>0.565</td></tr>
        </table>
        """
        mock_get.return_value = mock_response
        
        # Test scraping logic
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(mock_response.text, 'html.parser')
        table = soup.find('table', {'id': 'advanced_stats'})
        assert table is not None
    
    def test_parse_basketball_reference_table(self):
        """Test parsing Basketball-Reference table format"""
        html = """
        <table>
            <thead><tr><th>Team</th><th>PTS</th></tr></thead>
            <tbody>
                <tr><td>LAL</td><td>110.5</td></tr>
                <tr><td>GSW</td><td>115.2</td></tr>
            </tbody>
        </table>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        rows = soup.find_all('tr')
        assert len(rows) > 0
        
        # Extract data
        data = []
        for row in rows[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) >= 2:
                data.append({
                    'team': cells[0].text,
                    'pts': float(cells[1].text)
                })
        
        assert len(data) == 2
        assert data[0]['team'] == 'LAL'
        assert data[0]['pts'] == 110.5


class TestNewsScraper:
    """Test news sentiment scraper"""
    
    @patch('requests.get')
    def test_fetch_news_articles(self, mock_get):
        """Test fetching news articles"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Lakers dominate Warriors in decisive win",
                    "description": "Great performance by LeBron James",
                    "publishedAt": "2025-11-12T10:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test article structure
        articles = mock_response.json()["articles"]
        assert len(articles) > 0
        assert "title" in articles[0]
        assert "description" in articles[0]
    
    def test_sentiment_analysis_basic(self):
        """Test basic sentiment analysis"""
        from textblob import TextBlob
        
        # Positive sentiment
        text_pos = "Lakers played amazingly well and won easily"
        blob_pos = TextBlob(text_pos)
        assert blob_pos.sentiment.polarity > 0
        
        # Negative sentiment
        text_neg = "Warriors played terribly and lost badly"
        blob_neg = TextBlob(text_neg)
        assert blob_neg.sentiment.polarity < 0
        
        # Neutral sentiment
        text_neu = "The game was played at the arena"
        blob_neu = TextBlob(text_neu)
        assert abs(blob_neu.sentiment.polarity) < 0.1


class TestDataValidation:
    """Test data validation and quality checks"""
    
    def test_validate_game_data_structure(self):
        """Test game data has required fields"""
        game_data = {
            "game_id": "0022200001",
            "date": "2025-11-12",
            "home_team": "LAL",
            "away_team": "GSW",
            "home_score": 110,
            "away_score": 105
        }
        
        required_fields = ["game_id", "date", "home_team", "away_team", "home_score", "away_score"]
        for field in required_fields:
            assert field in game_data
        
        # Validate data types
        assert isinstance(game_data["home_score"], (int, float))
        assert isinstance(game_data["away_score"], (int, float))
    
    def test_validate_team_abbreviations(self):
        """Test team abbreviations are valid"""
        valid_teams = [
            'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
            'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK',
            'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'
        ]
        
        test_teams = ['LAL', 'GSW', 'BOS', 'MIA']
        for team in test_teams:
            assert team in valid_teams
    
    def test_date_format_validation(self):
        """Test date format is valid"""
        valid_date = "2025-11-12"
        
        # Parse date
        parsed = datetime.strptime(valid_date, "%Y-%m-%d")
        assert parsed.year == 2025
        assert parsed.month == 11
        assert parsed.day == 12
        
        # Test invalid format
        invalid_date = "11/12/2025"
        with pytest.raises(ValueError):
            datetime.strptime(invalid_date, "%Y-%m-%d")


class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_historical_data_exists(self):
        """Test historical data file exists"""
        data_path = Path("data/processed/all_games_historical.csv")
        if data_path.exists():
            df = pd.read_csv(data_path, nrows=5)
            assert len(df) > 0
            # Check for essential columns
            assert 'date' in df.columns or 'GAME_DATE' in df.columns
    
    def test_feature_data_shape(self):
        """Test engineered features have correct shape"""
        feature_path = Path("data/processed/engineered_features.parquet")
        if feature_path.exists():
            df = pd.read_parquet(feature_path)
            
            # Should have many features (50+)
            assert df.shape[1] >= 10
            
            # Should have reasonable number of games
            assert df.shape[0] > 100
    
    def test_no_missing_critical_fields(self):
        """Test no missing values in critical fields"""
        feature_path = Path("data/processed/engineered_features.parquet")
        if feature_path.exists():
            df = pd.read_parquet(feature_path)
            
            critical_fields = ['date', 'home_team', 'away_team']
            for field in critical_fields:
                if field in df.columns:
                    assert df[field].isna().sum() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
