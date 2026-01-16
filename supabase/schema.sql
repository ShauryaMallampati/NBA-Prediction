-- Supabase Tables for NBA Prediction System
-- Run this in the Supabase SQL Editor

-- =====================================
-- 1. PREDICTIONS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id TEXT NOT NULL,
    date DATE NOT NULL,
    home_team TEXT,
    away_team TEXT,
    prediction TEXT,  -- e.g., 'HOME' or 'AWAY'
    confidence FLOAT,
    home_win_prob FLOAT,
    away_win_prob FLOAT,
    spread FLOAT,
    over_under FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(game_id, date)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(date);
CREATE INDEX IF NOT EXISTS idx_predictions_game_id ON predictions(game_id);

-- =====================================
-- 2. EVALUATIONS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_games INT,
    correct INT,
    accuracy FLOAT,
    avg_confidence FLOAT,
    model_version TEXT,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_evaluations_date ON evaluations(date);

-- =====================================
-- 3. ANALYSIS TABLE (For AI explanations)
-- =====================================
CREATE TABLE IF NOT EXISTS analysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    prediction_id UUID REFERENCES predictions(id),
    date DATE NOT NULL,
    game_id TEXT,
    explanation TEXT,
    missed_factors TEXT[],
    storyline TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================
-- Enable Row Level Security (Optional but recommended)
-- =====================================
-- For public read access:
-- ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);

-- =====================================
-- Grant permissions to service role
-- =====================================
GRANT ALL ON predictions TO service_role;
GRANT ALL ON evaluations TO service_role;
GRANT ALL ON analysis TO service_role;
