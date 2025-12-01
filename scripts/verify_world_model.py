"""
Verify the World Model integration.
Checks if all components (Ensemble, RNN, CNN) are loadable and runnable.
"""
import sys
from pathlib import Path
import torch
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.world_model import world_model

def verify_world_model():
    print("\n" + "="*80)
    print("🌍 NBA WORLD MODEL VERIFICATION")
    print("="*80)
    
    # 1. Check Components
    print("\n1️⃣  Checking Components:")
    print(f"   • Ensemble Model: {'✅ Loaded' if world_model.ensemble.is_trained else '❌ Not Loaded (Train first)'}")
    print(f"   • Live RNN:       {'✅ Loaded' if world_model.live_rnn_loaded else '❌ Not Loaded (Train first)'}")
    print(f"   • Vision CNN:     {'✅ Loaded' if world_model.vision_cnn_loaded else '❌ Not Loaded (Train first)'}")
    
    # 2. Test Ensemble Prediction (if loaded)
    if world_model.ensemble.is_trained:
        print("\n2️⃣  Testing Ensemble Prediction...")
        # Create dummy features matching the model's expected features
        dummy_features = pd.DataFrame([np.random.rand(len(world_model.ensemble.feature_names))], 
                                      columns=world_model.ensemble.feature_names)
        try:
            pred = world_model.predict_pregame(dummy_features)
            print(f"   ✅ Prediction successful: {pred.iloc[0]['prediction']} ({pred.iloc[0]['home_win_probability']}%)")
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")
    else:
        print("\n2️⃣  Skipping Ensemble Test (Model not loaded)")

    # 3. Test Live RNN Prediction (if loaded)
    if world_model.live_rnn_loaded:
        print("\n3️⃣  Testing Live RNN Prediction...")
        # Dummy sequence: (seq_len=10, input_size=1) - Current model only uses score_diff
        dummy_seq = np.random.rand(10, 1) 
        try:
            prob = world_model.predict_live_win_prob(dummy_seq)
            print(f"   ✅ Prediction successful: Win Prob = {prob:.4f}")
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")
    else:
        print("\n3️⃣  Skipping Live RNN Test (Model not loaded)")

    # 4. Test Vision CNN Prediction (if loaded)
    if world_model.vision_cnn_loaded:
        print("\n4️⃣  Testing Vision CNN Prediction...")
        # Dummy clip: (Channels=3, Frames=16, Height=112, Width=112) - Standard R(2+1)D or similar input
        # MobileNetV3 usually takes (B, C, H, W) for images, but for video it might be different.
        # Let's assume the model expects standard image batch for now or check model definition.
        # The get_vision_model returns torchvision.models.mobilenet_v3_large.
        # It expects (B, C, H, W).
        dummy_img = torch.randn(3, 224, 224) 
        try:
            probs = world_model.analyze_video_clip(dummy_img)
            print(f"   ✅ Prediction successful: {probs}")
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")
    else:
        print("\n4️⃣  Skipping Vision CNN Test (Model not loaded)")

    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    verify_world_model()
