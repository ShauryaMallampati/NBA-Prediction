"""
Script to fetch basketball highlights and index them for the Vision CNN.
"""
import sys
import pandas as pd
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.highlights import highlights_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*80)
    print("🎥 FETCHING BASKETBALL HIGHLIGHTS")
    print("="*80)
    
    # Setup directories
    vision_dir = Path("artifacts/vision")
    clips_dir = vision_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    
    # Teams/Players to fetch
    queries = ["LeBron James", "Stephen Curry", "Lakers", "Celtics"]
    
    all_clips = []
    
    for query in queries:
        print(f"\n🔍 Searching for: {query}")
        results = highlights_api.get_highlights(search=query)
        
        if not results:
            print(f"   ⚠️ No results found (Check API Key)")
            # For demonstration/testing, we might want to create a dummy entry if API fails
            # so the pipeline doesn't break completely during dev
            continue
            
        print(f"   ✅ Found {len(results)} clips")
        
        for clip in results[:2]: # Limit to 2 per query to save space/time
            clip_id = clip.get('id', 'unknown')
            video_url = clip.get('video_url')
            title = clip.get('title', 'Untitled')
            
            if not video_url:
                continue
                
            # Download
            filename = f"{clip_id}.mp4"
            save_path = clips_dir / filename
            
            if not save_path.exists():
                if highlights_api.download_video(video_url, save_path):
                    all_clips.append({
                        'clip_id': clip_id,
                        'title': title,
                        'path': str(save_path),
                        'label': 1 if 'win' in title.lower() or 'dunk' in title.lower() else 0 # Dummy labeling logic
                    })
            else:
                print(f"   ⏩ Skipping existing: {filename}")
                all_clips.append({
                    'clip_id': clip_id,
                    'title': title,
                    'path': str(save_path),
                    'label': 1
                })

    # If API failed (likely due to no key), create a dummy index for verification purposes
    if not all_clips:
        print("\n⚠️ API fetch failed or returned no data. Creating dummy index for verification.")
        dummy_path = clips_dir / "dummy_clip.mp4"
        # Create a dummy file if it doesn't exist
        if not dummy_path.exists():
            with open(dummy_path, 'wb') as f:
                f.write(b'dummy video content')
        
        all_clips.append({
            'clip_id': 'dummy_001',
            'title': 'Dummy Clip',
            'path': str(dummy_path),
            'label': 0
        })

    # Save Index
    if all_clips:
        df = pd.DataFrame(all_clips)
        index_path = vision_dir / "clips.parquet"
        df.to_parquet(index_path)
        print(f"\n✅ Saved index to {index_path}")
        print(f"   Total clips: {len(df)}")
    else:
        print("\n❌ No clips to index.")

if __name__ == "__main__":
    main()
