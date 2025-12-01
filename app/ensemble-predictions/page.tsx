"use client"

import { AlertCircle, ArrowLeft, Brain, CheckCircle, RefreshCw, Target, Users } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

interface IndividualVote {
  [key: string]: string
}

interface EnsemblePrediction {
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
  individual_votes: IndividualVote
  home_odds: number
  away_odds: number
  home_spread: number
  away_spread: number
}

interface ModelInfo {
  num_models: number
  model_names: string[]
  num_features: number
  feature_names: string[]
}

interface PredictionsResponse {
  timestamp: string
  total_games: number
  predictions: EnsemblePrediction[]
  model_info: ModelInfo
}

export default function EnsemblePredictionsPage() {
  const [data, setData] = useState<PredictionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPredictions = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/predictions')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      setError("Failed to fetch predictions. Is the API server running?")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPredictions()
    // Refresh every 5 minutes
    const interval = setInterval(fetchPredictions, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return "text-green-400"
    if (confidence >= 50) return "text-yellow-400"
    return "text-orange-400"
  }

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 70) return "bg-green-500/20 border-green-500/30"
    if (confidence >= 50) return "bg-yellow-500/20 border-yellow-500/30"
    return "bg-orange-500/20 border-orange-500/30"
  }

  const getConsensusColor = (consensus: number) => {
    if (consensus >= 80) return "text-emerald-400"
    if (consensus >= 60) return "text-blue-400"
    return "text-purple-400"
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
      {/* Navigation Bar */}
      <nav className="bg-slate-900/95 backdrop-blur-lg border-b border-slate-700/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🏀
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tight text-white">NBA Intel</h1>
                <p className="text-xs text-slate-400">Ensemble ML Predictions</p>
              </div>
            </Link>
            
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors">
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </Link>
              <button
                onClick={fetchPredictions}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <Brain className="w-10 h-10 text-blue-400" />
            <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 text-transparent bg-clip-text">
              Ensemble Predictions
            </h1>
          </div>
          <p className="text-slate-300 text-lg mb-6">
            6 ML algorithms voting together for maximum accuracy
          </p>
          
          {data?.model_info && (
            <div className="flex flex-wrap gap-4">
              <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400">Models</div>
                <div className="text-lg font-bold text-white">{data.model_info.num_models}</div>
              </div>
              <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400">Features</div>
                <div className="text-lg font-bold text-white">{data.model_info.num_features}</div>
              </div>
              <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400">Total Games</div>
                <div className="text-lg font-bold text-white">{data.total_games}</div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
              <p className="text-slate-300">Loading ensemble predictions...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 backdrop-blur-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-red-400 mb-2">Error Loading Predictions</h3>
                <p className="text-red-300/80">{error}</p>
                <p className="text-sm text-slate-400 mt-2">
                  Make sure the API server is running: <code className="bg-slate-800 px-2 py-1 rounded">python3 src/api/ensemble_predictions.py</code>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Predictions Grid */}
        {!loading && !error && data && (
          <div className="space-y-6">
            {data.predictions.map((prediction, index) => (
              <div
                key={prediction.game_id}
                className="bg-slate-900/50 backdrop-blur-lg border border-slate-700/50 rounded-xl p-6 hover:border-blue-500/50 transition-all"
              >
                {/* Game Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
                      <span className="text-sm font-bold text-blue-400">#{index + 1}</span>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">Game Time</div>
                      <div className="font-semibold text-white">{formatTime(prediction.commence_time)}</div>
                    </div>
                  </div>
                  
                  <div className={`px-4 py-2 rounded-lg border ${getConfidenceBg(prediction.confidence)}`}>
                    <div className="text-xs text-slate-400 mb-1">Confidence</div>
                    <div className={`text-xl font-bold ${getConfidenceColor(prediction.confidence)}`}>
                      {prediction.confidence.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Teams & Prediction */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  {/* Home Team */}
                  <div className={`p-4 rounded-lg border-2 ${
                    prediction.prediction === 'HOME_WIN' 
                      ? 'bg-green-500/10 border-green-500/30' 
                      : 'bg-slate-800/30 border-slate-700/30'
                  }`}>
                    <div className="text-xs text-slate-400 mb-2">HOME</div>
                    <div className="text-xl font-bold text-white mb-3">{prediction.home_team}</div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-400">Win Probability</span>
                        <span className="text-lg font-bold text-green-400">
                          {prediction.home_win_probability.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs border-t border-slate-700/30 pt-2 mt-2">
                        <span className="text-slate-500">Odds: <span className="text-white">{prediction.home_odds}</span></span>
                        <span className="text-slate-500">Spread: <span className="text-white">{prediction.home_spread > 0 ? '+' : ''}{prediction.home_spread}</span></span>
                      </div>
                      {prediction.prediction === 'HOME_WIN' && (
                        <div className="flex items-center gap-2 text-green-400 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          <span className="font-semibold">Predicted Winner</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* VS Divider */}
                  <div className="flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-2xl font-black text-slate-500 mb-2">VS</div>
                      <div className={`text-sm ${getConsensusColor(prediction.consensus_percentage)}`}>
                        <Users className="w-4 h-4 inline mr-1" />
                        {prediction.models_agree} Models Agree
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {prediction.consensus_percentage.toFixed(0)}% Consensus
                      </div>
                    </div>
                  </div>

                  {/* Away Team */}
                  <div className={`p-4 rounded-lg border-2 ${
                    prediction.prediction === 'AWAY_WIN' 
                      ? 'bg-green-500/10 border-green-500/30' 
                      : 'bg-slate-800/30 border-slate-700/30'
                  }`}>
                    <div className="text-xs text-slate-400 mb-2">AWAY</div>
                    <div className="text-xl font-bold text-white mb-3">{prediction.away_team}</div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-400">Win Probability</span>
                        <span className="text-lg font-bold text-red-400">
                          {prediction.away_win_probability.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs border-t border-slate-700/30 pt-2 mt-2">
                        <span className="text-slate-500">Odds: <span className="text-white">{prediction.away_odds}</span></span>
                        <span className="text-slate-500">Spread: <span className="text-white">{prediction.away_spread > 0 ? '+' : ''}{prediction.away_spread}</span></span>
                      </div>
                      {prediction.prediction === 'AWAY_WIN' && (
                        <div className="flex items-center gap-2 text-green-400 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          <span className="font-semibold">Predicted Winner</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Individual Model Votes */}
                <div className="border-t border-slate-700/50 pt-4">
                  <div className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    Individual Model Votes
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    {Object.entries(prediction.individual_votes).map(([model, vote]) => (
                      <div
                        key={model}
                        className={`px-3 py-2 rounded-lg border text-center ${
                          vote === 'HOME' 
                            ? 'bg-green-500/10 border-green-500/30 text-green-400' 
                            : 'bg-red-500/10 border-red-500/30 text-red-400'
                        }`}
                      >
                        <div className="text-xs text-slate-400 mb-1">{model}</div>
                        <div className="text-sm font-bold">{vote}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Model Info */}
        {!loading && !error && data && (
          <div className="mt-12 bg-slate-900/50 backdrop-blur-lg border border-slate-700/50 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-400" />
              Ensemble Model Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="text-sm font-semibold text-slate-300 mb-2">Active Models ({data.model_info.num_models})</div>
                <div className="space-y-2">
                  {data.model_info.model_names.map(model => (
                    <div key={model} className="flex items-center gap-2 text-slate-400">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="capitalize">{model.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-300 mb-2">Features ({data.model_info.num_features})</div>
                <div className="flex flex-wrap gap-2">
                  {data.model_info.feature_names.slice(0, 10).map(feature => (
                    <span
                      key={feature}
                      className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded text-xs text-slate-400"
                    >
                      {feature}
                    </span>
                  ))}
                  {data.model_info.feature_names.length > 10 && (
                    <span className="px-2 py-1 text-xs text-slate-500">
                      +{data.model_info.feature_names.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
