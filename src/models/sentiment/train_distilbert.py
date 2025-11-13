"""
Train DistilBERT sentiment analysis model for NBA predictions.
Fine-tunes a pretrained DistilBERT model on sports sentiment data.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    AdamW,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split

# Determine device
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")
DATA_PATH = "artifacts/sentiment/sentiment_training.parquet"
OUT = Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

class SentimentDataset(Dataset):
    """PyTorch dataset for sentiment analysis"""
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_epoch(model, dataloader, optimizer, scheduler, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch in dataloader:
        optimizer.zero_grad()
        
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        loss = outputs.loss
        logits = outputs.logits
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        predictions = torch.argmax(logits, dim=1)
        correct += (predictions == labels).sum().item()
        total += labels.size(0)
    
    return total_loss / len(dataloader), correct / total

def eval_model(model, dataloader, device):
    """Evaluate model"""
    model.eval()
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=1)
            
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
    
    return correct / total

def main():
    print(f"\n{'='*60}")
    print(f"🤖 Training DistilBERT Sentiment Model")
    print(f"{'='*60}")
    print(f"Device: {DEVICE}")
    print(f"Data: {DATA_PATH}")
    print(f"Output: {OUT}\n")
    
    # Load data
    print("📥 Loading data...")
    df = pd.read_parquet(DATA_PATH)
    
    # Map sentiment to labels
    label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
    df['label'] = df['sentiment'].map(label_map)
    
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['text'].values,
        df['label'].values,
        test_size=0.2,
        random_state=42,
        stratify=df['label'].values
    )
    
    print(f"✅ Loaded {len(df):,} samples")
    print(f"   Train: {len(train_texts):,}")
    print(f"   Val: {len(val_texts):,}\n")
    
    # Initialize tokenizer and model
    print("🔧 Loading DistilBERT...")
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=3
    ).to(DEVICE)
    
    # Create datasets
    train_dataset = SentimentDataset(train_texts, train_labels, tokenizer)
    val_dataset = SentimentDataset(val_texts, val_labels, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16)
    
    # Setup optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=2e-5)
    total_steps = len(train_loader) * 3  # 3 epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )
    
    # Training loop
    print(f"🎯 Starting training (3 epochs)...\n")
    best_acc = 0
    
    for epoch in range(3):
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, scheduler, DEVICE
        )
        val_acc = eval_model(model, val_loader, DEVICE)
        
        print(f"Epoch {epoch+1}/3:")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"  Val Acc: {val_acc:.4f}\n")
        
        if val_acc > best_acc:
            best_acc = val_acc
            # Save best model
            model_path = OUT / "sentiment_distilbert"
            model.save_pretrained(model_path)
            tokenizer.save_pretrained(model_path)
            print(f"  💾 Saved best model (Val Acc: {val_acc:.4f})\n")
    
    print(f"✅ Training complete! Best val accuracy: {best_acc:.4f}")
    print(f"💾 Model saved to: {OUT / 'sentiment_distilbert'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
