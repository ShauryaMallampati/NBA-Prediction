'use client';

import { ArrowUpRight, Flame, TrendingUp, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';

interface GamePrediction {
  game_id: string;
  date: string;
  home_team: string;
  away_team: string;
  home_win_prob: number;
  away_win_prob: number;
  confidence: number;
  top_features?: Array<{ name: string; importance: number }>;
  model_version?: string;
  accuracy?: number;
}

export default function PredictionsPage() {
  const [games, setGames] = useState<GamePrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'high-confidence' | 'close'>('all');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await fetch(
          `/api/predictions?date=${new Date().toISOString().split('T')[0]}`
        );
        if (response.ok) {
          const data = await response.json();
          setGames(Array.isArray(data) ? data : data.games || []);
          setLastUpdate(new Date());
        }
      } catch (error) {
        console.error('Failed to load predictions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchPredictions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const filteredGames = games.filter((game) => {
    if (filter === 'high-confidence') {
      return game.confidence > 0.65;
    } else if (filter === 'close') {
      return Math.abs(game.home_win_prob - 0.5) < 0.1;
    }
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <Zap className="w-12 h-12 text-cyan-400 mx-auto mb-4 animate-pulse" />
            <p className="text-slate-400">Loading predictions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">🏀 NBA Predictions</h1>
              <p className="text-slate-400">AI-powered predictions • 63.83% accuracy • Updated every 5 minutes</p>
            </div>
            <div className="bg-gradient-to-br from-cyan-500 to-blue-600 px-6 py-3 rounded-lg text-center">
              <p className="text-white font-semibold text-lg">{filteredGames.length}</p>
              <p className="text-cyan-100 text-sm">Games Today</p>
            </div>
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-3 mb-4">
            {(['all', 'high-confidence', 'close'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === f
                    ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/50'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {f === 'all' ? '📊 All' : f === 'high-confidence' ? '🎯 High Confidence' : '⚖️ Close Games'}
              </button>
            ))}
          </div>

          {/* Last Update Info */}
          <p className="text-xs text-slate-500">
            ⏰ Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Games Grid */}
        <div className="grid gap-6 mb-8">
          {filteredGames.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Zap className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No games match this filter</p>
            </div>
          ) : (
            filteredGames.map((game) => (
              <GameCard key={game.game_id} game={game} />
            ))
          )}
        </div>

        {/* Model Info Footer */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center text-sm text-slate-400">
          <div className="flex items-center justify-center gap-2">
            <Flame className="w-4 h-4 text-orange-400" />
            <span>Model: XGBoost • ROC-AUC: 0.6701 • Sigmoid Calibrated</span>
            <Flame className="w-4 h-4 text-orange-400" />
          </div>
        </div>
      </div>
    </div>
  );
}

function GameCard({ game }: { game: GamePrediction }) {
  const homeWinProb = game.home_win_prob;
  const awayWinProb = game.away_win_prob;
  const homeIsHigher = homeWinProb > 0.5;

  return (
    <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-700/50 hover:border-cyan-500/50 transition-all p-6 rounded-lg shadow-lg hover:shadow-cyan-500/20">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Teams */}
        <div className="flex items-center justify-between md:justify-center gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-2">{game.home_team}</div>
            <span className="inline-block px-3 py-1 bg-cyan-500/20 text-cyan-400 text-xs font-semibold rounded-full border border-cyan-500/30">
              🏠 Home
            </span>
          </div>
          <div className="text-xl text-slate-500 font-light">vs</div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-2">{game.away_team}</div>
            <span className="inline-block px-3 py-1 bg-orange-500/20 text-orange-400 text-xs font-semibold rounded-full border border-orange-500/30">
              ✈️ Away
            </span>
          </div>
        </div>

        {/* Center: Probability Bars */}
        <div className="space-y-4">
          {/* Home Team Probability */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-white">{game.home_team} Win Probability</span>
              <span className={`text-lg font-bold ${homeIsHigher ? 'text-cyan-400' : 'text-slate-400'}`}>
                {(homeWinProb * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-700/30 rounded-full h-3 overflow-hidden border border-slate-600/50">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full rounded-full transition-all duration-500 shadow-lg shadow-cyan-500/50"
                style={{ width: `${homeWinProb * 100}%` }}
              />
            </div>
          </div>

          {/* Away Team Probability */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-white">{game.away_team} Win Probability</span>
              <span className={`text-lg font-bold ${!homeIsHigher ? 'text-orange-400' : 'text-slate-400'}`}>
                {(awayWinProb * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-700/30 rounded-full h-3 overflow-hidden border border-slate-600/50">
              <div
                className="bg-gradient-to-r from-orange-400 to-red-500 h-full rounded-full transition-all duration-500 shadow-lg shadow-orange-500/50"
                style={{ width: `${awayWinProb * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Right: Prediction & Confidence */}
        <div className="space-y-4">
          {/* Main Prediction */}
          <div className={`rounded-lg p-4 border-2 ${
            homeIsHigher 
              ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border-cyan-500/50' 
              : 'bg-gradient-to-br from-orange-500/20 to-red-600/20 border-orange-500/50'
          }`}>
            <div className="flex items-center gap-3 mb-2">
              {homeIsHigher ? (
                <>
                  <ArrowUpRight className="w-5 h-5 text-cyan-400" />
                  <span className="text-white font-bold text-lg">{game.home_team}</span>
                </>
              ) : (
                <>
                  <ArrowUpRight className="w-5 h-5 text-orange-400 transform scale-x-[-1]" />
                  <span className="text-white font-bold text-lg">{game.away_team}</span>
                </>
              )}
            </div>
            <p className="text-xs text-slate-400">Expected to win</p>
          </div>

          {/* Confidence Score */}
          <div className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 rounded-lg p-4 border border-slate-600/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400 font-medium">Model Confidence</span>
              <Flame className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">
              {(game.confidence * 100).toFixed(0)}%
            </div>
            <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden border border-slate-600/50">
              <div
                className="bg-gradient-to-r from-amber-400 via-orange-400 to-red-500 h-full transition-all duration-500"
                style={{ width: `${game.confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Top Feature */}
          {game.top_features && game.top_features.length > 0 && (
            <div className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/50">
              <p className="text-xs text-slate-500 mb-1">🔝 Top Factor</p>
              <p className="text-sm font-semibold text-white">{game.top_features[0].name}</p>
            </div>
          )}
        </div>
      </div>

      {/* Expandable Details */}
      <details className="mt-6 pt-6 border-t border-slate-700/50 cursor-pointer group">
        <summary className="text-sm text-slate-400 hover:text-cyan-400 font-semibold flex items-center gap-2 select-none">
          <span className="group-open:rotate-180 transition-transform">▶</span>
          <TrendingUp className="w-4 h-4" />
          View All Factors ({game.top_features?.length || 0})
        </summary>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {game.top_features?.map((feature, idx) => (
            <div key={idx} className="bg-slate-700/20 rounded-lg p-3 border border-slate-600/30 hover:border-slate-600/60 transition-all">
              <p className="text-xs text-slate-500 truncate mb-1">{feature.name}</p>
              <div className="w-full bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full rounded-full"
                  style={{ width: `${Math.min((feature.importance * 100), 100)}%` }}
                />
              </div>
              <p className="text-xs font-semibold text-white mt-1">{(feature.importance * 100).toFixed(1)}%</p>
            </div>
          ))}
        </div>
      </details>

      {/* Game Time */}
      <div className="mt-6 pt-6 border-t border-slate-700/50 flex items-center justify-between">
        <p className="text-xs text-slate-500">
          📅 {new Date(game.date).toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
          })} at {new Date(game.date).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          })}
        </p>
        <span className="text-xs px-2 py-1 bg-slate-700/50 text-slate-400 rounded-full border border-slate-600/50">
          ID: {game.game_id.substring(0, 8)}
        </span>
      </div>
    </div>
  );
}
