import os
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    """Check if .env exists and has required keys."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("💡 Please copy .env.example to .env and fill in your API keys.")
        return False

    load_dotenv()
    
    required_keys = [
        "NBA_STATS_API_KEY",
        "ODDS_API_KEY"
    ]
    
    missing = []
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == "your_key_here":
            missing.append(key)
            
    if missing:
        print(f"❌ Missing or default values for: {', '.join(missing)}")
        return False
        
    print("✅ Environment keys validated!")
    return True

if __name__ == "__main__":
    if validate_environment():
        exit(0)
    else:
        exit(1)
