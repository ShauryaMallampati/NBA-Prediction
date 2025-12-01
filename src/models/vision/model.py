import torch
from torch import nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
import os
import sys
import time

def get_vision_model(num_classes=5, pretrained=True):
    """
    Get MobileNetV3 Large model for vision tasks.
    Upgraded to Large variant for better accuracy.
    Shows download progress if weights are not cached.
    """
    weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
    model_url = weights.url if pretrained else None
    cache_dir = os.path.expanduser("~/.cache/torch/hub/checkpoints")
    model_filename = "mobilenet_v3_large-5c1a4163.pth"
    model_path = os.path.join(cache_dir, model_filename)

    if pretrained and not os.path.exists(model_path):
        print(f"\n⬇️ Downloading MobileNetV3 Large weights...")
        print(f"   URL: {model_url}")
        print(f"   Target: {model_path}")
        print(f"   Size: ~21 MB")
        sys.stdout.flush()
        start = time.time()
        # Use torch.hub.download_url_to_file for progress
        from torch.hub import download_url_to_file
        def progress(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            mb = int(count * block_size / 1024 / 1024)
            sys.stdout.write(f"\r   Downloaded: {mb} MB ({percent}%)")
            sys.stdout.flush()
        download_url_to_file(model_url, model_path, progress=progress)
        print(f"\n✅ Download complete in {time.time()-start:.1f}s\n")
    else:
        print(f"\n✅ MobileNetV3 Large weights already cached.")
        print(f"   Path: {model_path}")
        sys.stdout.flush()

    model = mobilenet_v3_large(weights=weights)
    
    # Replace classifier head
    # MobileNetV3 classifier structure:
    # (0): Linear
    # (1): Hardswish
    # (2): Dropout
    # (3): Linear (Output)
    
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    
    return model
