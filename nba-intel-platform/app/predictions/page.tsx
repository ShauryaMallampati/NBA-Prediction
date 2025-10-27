'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, TrendingUp, TrendingDown, Zap } from 'lucide-react';

interface PredictionResult {
  raw: number;
  calibrated: number;
  over: boolean;
  confidence: number;
}

interface LivePrediction {
  player_name: string;
  predictions: {
    [key: string]: PredictionResult;
  };
  ready_for_production: boolean;
  error?: string;
}

const StatColors = {
  PTS: 'from-red-500 to-orange-500',
  AST: 'from-blue-500 to-cyan-500',
  REB: 'from-green-500 to-emerald-500',
  STL: 'from-purple-500 to-pink-500',
  BLK: 'from-yellow-500 to-amber-500',
};

const StatEmojis = {
  PTS: '🏀',
  AST: '🎯',
  REB: '📦',
  STL: '🔒',
  BLK: '🚫',
};

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<LivePrediction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playerName, setPlayerName] = useState('LeBron James');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchPredictions = async (playerNameInput: string = playerName) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/predictions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_name: playerNameInput,
          is_home: true,
          rest_days: 2,
          is_back_to_back: false,
          FG_pct: 0.50,
          FG3_pct: 0.38,
          FT_pct: 0.73,
          usage_pct: 0.28,
          games_played: 15,
          consistency_score: 0.85,
          recent_stats: {
            PTS_3game: 25.3,
            PTS_7game: 24.8,
            PTS_7game_std: 2.1,
            AST_3game: 7.2,
            AST_7game: 7.0,
            AST_7game_std: 0.9,
            REB_3game: 7.8,
            REB_7game: 7.5,
            REB_7game_std: 1.2,
            STL_3game: 1.3,
            STL_7game: 1.2,
            STL_7game_std: 0.3,
            BLK_3game: 0.7,
            BLK_7game: 0.65,
            BLK_7game_std: 0.2,
            PTS_trend: 0.5,
            AST_trend: 0.3,
            REB_trend: -0.2,
          },
          season_stats: {
            PTS_avg: 24.5,
            AST_avg: 6.8,
            REB_avg: 7.2,
            STL_avg: 1.1,
            BLK_avg: 0.6,
          },
          opponent_defense: {
            def_PTS_allowed: 108,
            def_AST_allowed: 26,
            def_REB_allowed: 44,
            def_STL_allowed: 7.5,
            def_BLK_allowed: 4.8,
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPredictions(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch predictions';
      setError(errorMessage);
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchPredictions();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, playerName]);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-red-600';
    if (confidence >= 0.6) return 'text-orange-600';
    if (confidence >= 0.4) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const StatPredictionCard = ({ stat, prediction }: { stat: string; prediction: PredictionResult }) => {
    const isOver = prediction.over;
    const confidence = (prediction.confidence * 100).toFixed(1);

    return (
      <div className={`relative overflow-hidden rounded-lg border border-gray-200 bg-gradient-to-br ${StatColors[stat as keyof typeof StatColors]} p-6 text-white shadow-md transition-transform hover:scale-105`}>
        <div className="relative z-10">
          {/* Header */}
          <div className="mb-3 flex items-center justify-between">
            <span className="text-3xl">{StatEmojis[stat as keyof typeof StatEmojis]}</span>
            <Badge className={isOver ? 'bg-green-600' : 'bg-red-600'}>
              {isOver ? 'OVER' : 'UNDER'}
            </Badge>
          </div>

          {/* Stat name */}
          <h3 className="mb-2 text-lg font-bold">{stat}</h3>

          {/* Calibrated probability */}
          <div className="mb-3 space-y-1">
            <div className="text-sm opacity-90">Probability</div>
            <div className="text-3xl font-bold">{(prediction.calibrated * 100).toFixed(1)}%</div>
          </div>

          {/* Confidence meter */}
          <div className="space-y-1">
            <div className="text-xs opacity-90">Confidence</div>
            <div className="flex items-center space-x-2">
              <div className="h-2 flex-1 rounded-full bg-white/20">
                <div
                  className="h-full rounded-full bg-white/80 transition-all"
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <span className={`text-sm font-bold ${getConfidenceColor(Number(confidence) / 100)}`}>
                {confidence}%
              </span>
            </div>
          </div>

          {/* Raw vs Calibrated */}
          <div className="mt-3 text-xs opacity-75">
            Raw: {(prediction.raw * 100).toFixed(1)}%
          </div>
        </div>

        {/* Background accent */}
        <div className="absolute right-0 top-0 opacity-10">
          <Zap className="h-32 w-32" />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 p-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Live Predictions</h1>
        <p className="text-gray-600">Real-time player prop predictions powered by LightGBM</p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">Player Name</label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Enter player name"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <button
              onClick={() => fetchPredictions()}
              disabled={loading}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Loading...' : 'Predict'}
            </button>
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Auto-refresh every 30 seconds</span>
          </label>
        </CardContent>
      </Card>

      {/* Error state */}
      {error && (
        <div className="flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && !predictions && (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-40 rounded-lg bg-gray-200 animate-pulse" />
          ))}
        </div>
      )}

      {/* Predictions */}
      {predictions && !loading && (
        <div className="space-y-6">
          {/* Player info */}
          <div className="rounded-lg border border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
            <h2 className="text-2xl font-bold text-gray-900">{predictions.player_name}</h2>
            <div className="mt-2 flex items-center gap-2">
              <Badge className={predictions.ready_for_production ? 'bg-green-600' : 'bg-yellow-600'}>
                {predictions.ready_for_production ? '✓ Production Ready' : '⚠ Still Initializing'}
              </Badge>
            </div>
          </div>

          {/* Predictions grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {Object.entries(predictions.predictions).map(([stat, prediction]) => (
              <StatPredictionCard key={stat} stat={stat} prediction={prediction} />
            ))}
          </div>

          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
              <CardDescription>Prediction overview and statistics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-gradient-to-br from-green-50 to-emerald-50 p-4">
                  <div className="text-sm text-gray-600">OVER Predictions</div>
                  <div className="text-3xl font-bold text-green-700">
                    {Object.values(predictions.predictions).filter((p) => p.over).length} / 5
                  </div>
                </div>
                <div className="rounded-lg bg-gradient-to-br from-red-50 to-orange-50 p-4">
                  <div className="text-sm text-gray-600">UNDER Predictions</div>
                  <div className="text-3xl font-bold text-red-700">
                    {Object.values(predictions.predictions).filter((p) => !p.over).length} / 5
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-gradient-to-br from-blue-50 to-cyan-50 p-4">
                  <div className="text-sm text-gray-600">Avg Confidence</div>
                  <div className="text-3xl font-bold text-blue-700">
                    {(
                      (Object.values(predictions.predictions).reduce((sum, p) => sum + p.confidence, 0) /
                        Object.values(predictions.predictions).length) *
                      100
                    ).toFixed(1)}
                    %
                  </div>
                </div>
                <div className="rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 p-4">
                  <div className="text-sm text-gray-600">Avg Calibrated Prob</div>
                  <div className="text-3xl font-bold text-purple-700">
                    {(
                      (Object.values(predictions.predictions).reduce((sum, p) => sum + p.calibrated, 0) /
                        Object.values(predictions.predictions).length) *
                      100
                    ).toFixed(1)}
                    %
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
