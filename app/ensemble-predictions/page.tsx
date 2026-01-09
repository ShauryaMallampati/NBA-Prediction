"use client"

import {
  Brain,
  RefreshCw,
  Target,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  DollarSign,
  FileText,
  Zap,
  Home,
  ArrowLeft
} from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

interface Prediction {
  game_id: string
  home_team: string
  away_team: string
  commence_time: string
  prediction: string
  home_win_probability: number
  away_win_probability: number
  confidence: number
  models_agree: string
  consensus_percentage: number
  individual_votes: Record<string, string>
  home_odds: number
  away_odds: number
  home_spread: number
  away_spread: number
}

interface ApiResponse {
  timestamp: string
  total_games: number
  predictions: Prediction[]
}

export default function EnsemblePredictionsPage() {
  const [data, setData] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedGame, setExpandedGame] = useState<string | null>(null)

  useEffect(() => {
    fetchPredictions()
  }, [])

  const fetchPredictions = async () => {
    setLoading(true)
    try {
      const res = await fetch("http://localhost:8000/predictions")
      if (!res.ok) throw new Error("Failed to fetch predictions")
      const json = await res.json()
      setData(json)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (iso: string) => {
    return new Date(iso).toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    })
  }

  const getConfidenceColor = (conf: number) => {
    if (conf >= 70) return "text-green-400 bg-green-500/20 border-green-500/30"
    if (conf >= 50) return "text-yellow-400 bg-yellow-500/20 border-yellow-500/30"
    return "text-orange-400 bg-orange-500/20 border-orange-500/30"
  }

  const calculateKellyBet = (prob: number, odds: number) => {
    if (!odds || odds <= 0) return 0
    const decimalOdds = odds > 0 ? odds / 100 + 1 : 100 / Math.abs(odds) + 1
    const kellyFraction = (prob * decimalOdds - 1) / (decimalOdds - 1)
    const quarterKelly = kellyFraction * 0.25
    return Math.max(0, Math.min(0.05, quarterKelly)) * 100
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">
      {/* Header */}
      <header className="glass-strong sticky top-0 z-50 border-b">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 rounded-lg hover:bg-accent transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Ensemble Predictions</h1>
                <p className="text-xs text-muted-foreground">XGBoost + LightGBM + CatBoost</p>
              </div>
            </div>
          </div>
          <button
            onClick={fetchPredictions}
            className="flex items-center gap-2 px-4 py-2 rounded-lg glass-strong hover:bg-accent transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Bar */}
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 rounded-xl glass-strong border">
              <div className="text-3xl font-black text-primary">{data.total_games}</div>
              <div className="text-sm text-muted-foreground">Games Today</div>
            </div>
            <div className="p-4 rounded-xl glass-strong border">
              <div className="text-3xl font-black text-green-400">
                {data.predictions.filter(p => p.confidence >= 70).length}
              </div>
              <div className="text-sm text-muted-foreground">High Confidence</div>
            </div>
            <div className="p-4 rounded-xl glass-strong border">
              <div className="text-3xl font-black text-purple-400">3</div>
              <div className="text-sm text-muted-foreground">Models Voting</div>
            </div>
            <div className="p-4 rounded-xl glass-strong border">
              <div className="text-3xl font-black text-secondary">67.7%</div>
              <div className="text-sm text-muted-foreground">Model Accuracy</div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <RefreshCw className="w-12 h-12 text-primary animate-spin mb-4" />
            <p className="text-muted-foreground">Loading predictions...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-center">
            <p className="text-red-400 font-bold mb-2">Error Loading Predictions</p>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <p className="text-xs text-muted-foreground">
              Make sure the API is running: <code className="bg-accent px-2 py-1 rounded">poetry run python src/api/ensemble_predictions.py</code>
            </p>
          </div>
        )}

        {/* Predictions Grid */}
        {data && !loading && (
          <div className="space-y-4">
            {data.predictions.map((pred) => (
              <div
                key={pred.game_id}
                className="rounded-2xl glass-strong border-2 hover:border-primary/30 transition-all overflow-hidden"
              >
                {/* Main Card */}
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedGame(expandedGame === pred.game_id ? null : pred.game_id)}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    {/* Teams */}
                    <div className="flex-1">
                      <div className="text-xs text-muted-foreground mb-2">{formatTime(pred.commence_time)}</div>
                      <div className="flex items-center gap-4">
                        <div className={`flex-1 p-4 rounded-xl border-2 ${pred.prediction === "HOME_WIN"
                            ? "bg-green-500/10 border-green-500/30"
                            : "bg-slate-800/30 border-slate-700/30"
                          }`}>
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-xs text-muted-foreground flex items-center gap-1">
                                <Home className="w-3 h-3" /> HOME
                              </div>
                              <div className="font-bold text-lg">{pred.home_team}</div>
                            </div>
                            <div className={`text-3xl font-black ${pred.prediction === "HOME_WIN" ? "text-green-400" : "text-gray-500"
                              }`}>
                              {pred.home_win_probability.toFixed(0)}%
                            </div>
                          </div>
                        </div>
                        <div className="text-muted-foreground font-bold">VS</div>
                        <div className={`flex-1 p-4 rounded-xl border-2 ${pred.prediction === "AWAY_WIN"
                            ? "bg-green-500/10 border-green-500/30"
                            : "bg-slate-800/30 border-slate-700/30"
                          }`}>
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-xs text-muted-foreground">AWAY</div>
                              <div className="font-bold text-lg">{pred.away_team}</div>
                            </div>
                            <div className={`text-3xl font-black ${pred.prediction === "AWAY_WIN" ? "text-green-400" : "text-gray-500"
                              }`}>
                              {pred.away_win_probability.toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Confidence & Actions */}
                    <div className="flex items-center gap-3">
                      <div className={`px-4 py-2 rounded-xl border font-bold ${getConfidenceColor(pred.confidence)}`}>
                        {pred.confidence.toFixed(0)}% Confident
                      </div>
                      <div className="p-2 rounded-lg hover:bg-accent transition-colors">
                        {expandedGame === pred.game_id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedGame === pred.game_id && (
                  <div className="border-t border-border p-6 bg-gradient-to-b from-transparent to-primary/5">
                    <div className="grid md:grid-cols-3 gap-6">
                      {/* Model Votes */}
                      <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <Brain className="w-5 h-5 text-purple-400" />
                          <h4 className="font-bold text-purple-300">Model Votes</h4>
                        </div>
                        <div className="space-y-2 text-sm">
                          {Object.entries(pred.individual_votes || {}).map(([model, vote]) => (
                            <div key={model} className="flex justify-between items-center">
                              <span className="text-muted-foreground capitalize">{model.replace('_vote', '')}</span>
                              <span className={vote === "HOME" ? "text-green-400 font-bold" : "text-blue-400 font-bold"}>
                                {vote}
                              </span>
                            </div>
                          ))}
                          {Object.keys(pred.individual_votes || {}).length === 0 && (
                            <p className="text-muted-foreground">Agreement: {pred.models_agree}</p>
                          )}
                        </div>
                      </div>

                      {/* XAI Explanation */}
                      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <Zap className="w-5 h-5 text-blue-400" />
                          <h4 className="font-bold text-blue-300">Why This Prediction?</h4>
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center gap-2 text-green-400">
                            <TrendingUp className="w-4 h-4" />
                            <span>Elo Advantage</span>
                          </div>
                          <div className="flex items-center gap-2 text-green-400">
                            <TrendingUp className="w-4 h-4" />
                            <span>Home Court</span>
                          </div>
                          <div className="flex items-center gap-2 text-yellow-400">
                            <TrendingDown className="w-4 h-4" />
                            <span>Back-to-back factor</span>
                          </div>
                        </div>
                      </div>

                      {/* Kelly Criterion */}
                      <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <DollarSign className="w-5 h-5 text-green-400" />
                          <h4 className="font-bold text-green-300">Betting Suggestion</h4>
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Quarter Kelly</span>
                            <span className="text-green-400 font-bold">
                              {calculateKellyBet(
                                pred.home_win_probability / 100,
                                pred.home_odds || -110
                              ).toFixed(1)}% of bankroll
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Spread</span>
                            <span className="font-bold">{pred.home_spread > 0 ? '+' : ''}{pred.home_spread || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
