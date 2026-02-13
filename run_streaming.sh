#!/bin/bash
# Auto-setup and run streaming model

cd /Users/shauryamallampati/Desktop/NBA-Prediciton

echo "📦 Installing dependencies..."
pip install -q google-auth google-auth-httplib2 google-auth-oauthlib google-api-python-client 2>/dev/null

echo "🚀 Starting streaming world model (Google Drive edition)..."
python -u scripts/eval/streaming_world_model_gdrive.py --season 2025-26
