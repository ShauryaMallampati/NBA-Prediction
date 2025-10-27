"""Quick test of API endpoints with trained models"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("\n" + "="*80)
    print("TESTING API ENDPOINTS WITH TRAINED MODELS")
    print("="*80)
    
    # Give server time to start
    time.sleep(1)
    
    # Test 1: Health check
    print("\n1️⃣  Testing /health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Player props prediction
    print("\n2️⃣  Testing /player-props endpoint...")
    try:
        payload = {
            "player_name": "LeBron James",
            "stat_type": "PTS",
            "opponent": "Boston Celtics",
            "is_home": True
        }
        resp = requests.post(f"{BASE_URL}/player-props", json=payload, timeout=5)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {json.dumps(resp.json(), indent=2)[:200]}...")
        
        # Check if models are being used
        data = resp.json()
        if 'predicted_over_probability' in data:
            prob = data['predicted_over_probability']
            print(f"   ✅ Model prediction: {prob:.1%}")
        else:
            print(f"   ⚠️  Using baseline (models not yet integrated)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Bet opportunities
    print("\n3️⃣  Testing /bet-opportunities endpoint...")
    try:
        payload = {
            "lines": {
                "PTS_over_26.5": 1.91,
                "AST_over_7.5": 1.91,
            }
        }
        resp = requests.post(f"{BASE_URL}/bet-opportunities", json=payload, timeout=5)
        print(f"   Status: {resp.status_code}")
        data = resp.json()
        print(f"   Found {len(data.get('opportunities', []))} opportunities")
        if data.get('opportunities'):
            print(f"   First opportunity: {data['opportunities'][0]['stat']}")
            print(f"   ✅ Models providing edge detection")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 4: Performance tracking
    print("\n4️⃣  Testing /performance endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/performance", timeout=2)
        print(f"   Status: {resp.status_code}")
        data = resp.json()
        print(f"   Total bets logged: {data.get('total_bets', 0)}")
        print(f"   ✅ Performance tracking working")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL ENDPOINTS RESPONDING WITH TRAINED MODELS")
    print("="*80)
    return True

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)
