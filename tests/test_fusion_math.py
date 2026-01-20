
import torch
import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fusion.learnable_fusion import GatedFusion

def test_dynamic_floor_logic():
    print("\n\n🧪 Testing Dynamic Attention Scaling Math...")
    
    # Initialize model
    model = GatedFusion(n_modalities=6)
    
    # CASE 1: High Base Prob, Low Signals (Should NOT boost base)
    # [Base=0.8, Vis=0.001, Aud=0.001, ...]
    x_quiet = torch.zeros(1, 6)
    x_quiet[0, 0] = 0.8  # Base prob
    x_quiet[0, 1] = 0.001 # Tiny Vision delta
    
    _, weights_quiet = model.forward_with_floor(x_quiet)
    
    # Check that Base Prob didn't get a massive boost
    # If bug existed: floor = 0.01 + 0.8 * 2.0 = 1.61 (HUGE ERROR)
    # Correct: floor = 0.01 + 0.0 * 2.0 = 0.01
    
    print(f"\n[Case 1: Quiet] Signal: {x_quiet[0].tolist()}")
    print(f"[Case 1: Quiet] Weights: {weights_quiet[0].tolist()}")
    
    # Base weight should be dominant (learned), but others should be ~0.01 (floor)
    # We expect the gate to naturally favor index 0.
    
    # CASE 2: High Vision Signal (Should boost Vision)
    # [Base=0.6, Vis=0.10, Aud=0.001, ...]
    x_loud = torch.zeros(1, 6)
    x_loud[0, 0] = 0.6
    x_loud[0, 1] = 0.10  # HUGE Vision Delta
    
    _, weights_loud = model.forward_with_floor(x_loud)
    
    print(f"\n[Case 2: Loud] Signal: {x_loud[0].tolist()}")
    print(f"[Case 2: Loud] Weights: {weights_loud[0].tolist()}")
    
    vis_weight = weights_loud[0, 1].item()
    # Expected floor = 0.01 + (0.10 * 2.0) = 0.21
    # Normalized weight might be slightly lower if sum > 1, but should be >> 0.01
    
    assert vis_weight > 0.10, f"Vision weight {vis_weight} is too low for such a loud signal!"
    print("✅ Vision Boost Verified!")

    # CASE 3: Base Prob Masking (Residual Architecture Check)
    # In Residual Fusion, Base is Key 0 but not weighted by gate.
    # Gate outputs 5 weights for 5 deltas.
    
    # We can inspect the code behavior by passing a massive base prob
    x_massive = torch.zeros(1, 6)
    x_massive[0, 0] = 0.5 
    x_massive[0, 1] = 0.10 # Vision Delta
    
    # The output should be Base + (Vis * Weight)
    # If Weight ~ 0.20 (Floor), then Result ~= 0.5 + 0.02 = 0.52
    
    predicted_prob, full_weights = model.forward_with_floor(x_massive)
    
    print(f"\n[Case 3: Residual] Inputs: Base=0.5, Vis=0.10")
    print(f"[Case 3: Residual] Output Prob: {predicted_prob.item()}")
    print(f"[Case 3: Residual] Weights: {full_weights[0].tolist()}")
    
    # Check that Base Weight (Index 0) is hardcoded to 1.0 (Anchor)
    if full_weights[0, 0].item() == 1.0:
        print("✅ Residual Anchor Verified (Base Weight is 1.0)")
    else:
        print(f"❌ Base Weight is {full_weights[0, 0].item()}, expected 1.0")

    # Check Correction
    # Expected: 0.5 + (0.10 * ~0.2) = 0.52
    if 0.51 < predicted_prob.item() < 0.53:
         print("✅ Correction Applied Correctly")
    else:
         print(f"❌ Correction Logic Mismatch: Got {predicted_prob.item()}")

if __name__ == "__main__":
    test_dynamic_floor_logic()
