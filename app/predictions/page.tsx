"use client"

import { AlertCircle, ArrowLeft, Brain, RefreshCw, Target, TrendingUp, Users } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

interface ModelVotes {
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
  individual_votes: ModelVotes
  home_odds: number
  away_odds: number
  home_spread: number
  away_spread: number
}

interface PredictionsResponse {
  timestamp: string
  total_games: number
  predictions: EnsemblePrediction[]
}

export default function PredictionsPage() {
  const [data, setData] = useState<PredictionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const fetchPredictions = async (dateParam?: string) => {
    setLoading(true)
    setError(null)

    try {
      // Try FastAPI backend first
      let response = await fetch('http://localhost:8000/predictions')
      let result = null

      if (response.ok) {
        result = await response.json()

        // Handle both formats: {predictions: []} or direct list
        if (Array.isArray(result)) {
          result = {
            timestamp: new Date().toISOString(),
            total_games: result.length,
            predictions: result.map((p: any) => ({
              game_id: p.game_id || `${p.home_team}@${p.away_team}`,
              home_team: p.home_team || '',
              away_team: p.away_team || '',
              commence_time: p.date || p.commence_time || new Date().toISOString(),
              prediction: p.predicted_winner || (p.home_win_prob > 0.5 ? p.home_team : p.away_team),
              home_win_probability: p.home_win_prob || p.home_win_probability || 0.5,
              away_win_probability: p.away_win_prob || p.away_win_probability || 0.5,
              confidence: p.confidence || Math.abs((p.home_win_prob || 0.5) - 0.5) * 2 * 100,
              models_agree: 'ensemble',
              consensus_percentage: p.confidence || Math.abs((p.home_win_prob || 0.5) - 0.5) * 2 * 100,
              individual_votes: {},
              home_odds: p.home_odds || 0,
              away_odds: p.away_odds || 0,
              home_spread: p.home_spread || 0,
              away_spread: p.away_spread || 0,
            }))
          }
        }
      } else {
        // Fallback to Next.js API route
        const dateQuery = dateParam || new Date().toISOString().split('T')[0]
        response = await fetch(`/api/predictions?date=${dateQuery}`)

        if (response.ok) {
          const apiResult = await response.json()
          if (apiResult.success && apiResult.predictions) {
            result = {
              timestamp: new Date().toISOString(),
              total_games: apiResult.count || apiResult.predictions.length,
              predictions: apiResult.predictions.map((p: any) => ({
                game_id: p.game_id || `${p.home_team}@${p.away_team}`,
                home_team: p.home_team || '',
                away_team: p.away_team || '',
                commence_time: p.date || p.commence_time || new Date().toISOString(),
                prediction: p.predicted_winner || (parseFloat(p.home_win_prob) > 0.5 ? p.home_team : p.away_team),
                home_win_probability: parseFloat(p.home_win_prob) || 0.5,
                away_win_probability: parseFloat(p.away_win_prob) || 0.5,
                confidence: parseFloat(p.confidence) || Math.abs(parseFloat(p.home_win_prob || '0.5') - 0.5) * 2 * 100,
                models_agree: 'ensemble',
                consensus_percentage: parseFloat(p.confidence) || Math.abs(parseFloat(p.home_win_prob || '0.5') - 0.5) * 2 * 100,
                individual_votes: {},
                home_odds: 0,
                away_odds: 0,
                home_spread: 0,
                away_spread: 0,
              }))
            }
          }
        }
      }

      if (!result || !result.predictions || result.predictions.length === 0) {
        throw new Error(result?.message || 'No predictions available')
      }

      // If a specific date is selected, filter predictions for that date
      if (dateParam) {
        const filteredPredictions = result.predictions.filter(
          (p: EnsemblePrediction) => p.commence_time.startsWith(dateParam)
        )
        setData({
          ...result,
          predictions: filteredPredictions
        })
        setSelectedDate(dateParam)
      } else {
        setData(result)
      }
      setError(null)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to fetch predictions"
      setError(errorMsg)
      console.error('Prediction fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Check if date is in URL params
    const params = new URLSearchParams(window.location.search)
    const dateParam = params.get('date')

    if (dateParam) {
      fetchPredictions(dateParam)
    } else {
      fetchPredictions()
    }

    // Refresh every 5 minutes
    const interval = setInterval(() => {
      if (dateParam) {
        fetchPredictions(dateParam)
      } else {
        fetchPredictions()
      }
    }, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return "text-green-400"
    if (confidence >= 60) return "text-yellow-400"
    return "text-orange-400"
  }

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 70) return "bg-green-500/20 border-green-400/50"
    if (confidence >= 60) return "bg-yellow-500/20 border-yellow-400/50"
    return "bg-orange-500/20 border-orange-400/50"
  }

  const predictions = data?.predictions || []

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
                <p className="text-xs text-slate-400">ML-Powered Analytics</p>
              </div>
            </Link>

            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors">
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </Link>
              <Link href="/ensemble-predictions" className="text-sm text-slate-300 hover:text-blue-400 transition-colors">
                Detailed View
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/50">
              <Target className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Game Predictions
          </h1>
          <p className="text-slate-300 text-xl mb-8">
            AI-powered predictions using 6-model ensemble voting
          </p>

          <div className="flex flex-wrap justify-center gap-3 mb-6">
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-purple-600/30 border border-purple-400/50">
              <Users className="w-5 h-5 text-purple-300" />
              <span className="text-sm text-white font-semibold">6 Models Voting</span>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-green-600/30 border border-green-400/50">
              <TrendingUp className="w-5 h-5 text-green-300" />
              <span className="text-sm text-white font-semibold">100% Train Accuracy</span>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600/30 border border-blue-400/50">
              <Brain className="w-5 h-5 text-blue-300" />
              <span className="text-sm text-white font-semibold">Real-time Updates</span>
            </div>
          </div>

          <button
            onClick={() => fetchPredictions(selectedDate || undefined)}
            disabled={loading}
            className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-xl transition-all shadow-lg hover:shadow-blue-500/50 font-semibold"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Predictions
          </button>
        </div>

        {/* Model Performance Stats */}
        {!loading && predictions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2 font-semibold">High Confidence</p>
                  <p className="text-4xl font-black text-green-400">
                    {predictions.filter((p: EnsemblePrediction) => p.confidence >= 65).length}
                  </p>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-green-600/30 border border-green-400/50 flex items-center justify-center">
                  <TrendingUp className="w-8 h-8 text-green-400" />
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-3 font-medium">≥65% confidence</p>
            </div>

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2 font-semibold">Medium Confidence</p>
                  <p className="text-4xl font-black text-yellow-400">
                    {predictions.filter((p: EnsemblePrediction) => p.confidence >= 55 && p.confidence < 65).length}
                  </p>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-yellow-600/30 border border-yellow-400/50 flex items-center justify-center">
                  <TrendingUp className="w-8 h-8 text-yellow-400" />
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-3 font-medium">55-64% confidence</p>
            </div>

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2 font-semibold">Close Games</p>
                  <p className="text-4xl font-black text-orange-400">
                    {predictions.filter((p: EnsemblePrediction) => p.confidence < 55).length}
                  </p>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-orange-600/30 border border-orange-400/50 flex items-center justify-center">
                  <AlertCircle className="w-8 h-8 text-orange-400" />
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-3 font-medium">&lt;55% confidence</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 mb-8 border border-yellow-500/50">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-8 h-8 text-yellow-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <p className="text-yellow-400 font-bold text-xl mb-3">Connection Error</p>
                <p className="text-slate-300 text-lg mb-4">{error}</p>
                <div className="bg-slate-900/80 rounded-xl p-6 border border-slate-700/50 mb-4">
                  <p className="text-white font-semibold mb-3">To use this feature:</p>
                  <ul className="space-y-2 text-slate-300 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-1">1.</span>
                      <span>Start the API server: <code className="bg-slate-950 px-2 py-1 rounded text-blue-300">poetry run python src/api/ensemble_predictions.py</code></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-1">2.</span>
                      <span>Ensure it's running on <code className="bg-slate-950 px-2 py-1 rounded text-blue-300">localhost:8000</code></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-1">3.</span>
                      <span>Click "Refresh Predictions" to load the data</span>
                    </li>
                  </ul>
                </div>
                <button
                  onClick={() => fetchPredictions(selectedDate || undefined)}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2"
                >
                  <RefreshCw className="w-5 h-5" />
                  Retry
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-300 mt-6 text-lg">Loading predictions...</p>
          </div>
        )}

        {/* Predictions Grid */}
        {!loading && !error && predictions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {predictions.map((pred: EnsemblePrediction) => (
              <div
                key={pred.game_id}
                className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 hover:shadow-xl hover:shadow-blue-500/20 transition-all border-2 border-slate-700/50 hover:border-blue-500/50"
              >
                {/* Matchup */}
                <div className="flex items-center justify-between mb-8">
                  <div className="text-center flex-1">
                    <div className="text-4xl font-black text-white mb-2">{pred.away_team}</div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Away</div>
                  </div>

                  <div className="px-6">
                    <div className="text-3xl font-black text-slate-600">@</div>
                  </div>

                  <div className="text-center flex-1">
                    <div className="text-4xl font-black text-white mb-2">{pred.home_team}</div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Home</div>
                  </div>
                </div>

                {/* Probabilities */}
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <div className="text-center p-6 rounded-xl bg-slate-900/80 border border-slate-700/50">
                    <div className={`text-5xl font-black mb-3 ${pred.prediction === pred.away_team ? 'text-blue-400' : 'text-slate-600'}`}>
                      {(pred.away_win_probability).toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Win Probability</div>
                    <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <div className="text-slate-500">Odds</div>
                        <div className="text-white font-mono">{pred.away_odds}</div>
                      </div>
                      <div>
                        <div className="text-slate-500">Spread</div>
                        <div className="text-white font-mono">{pred.away_spread > 0 ? '+' : ''}{pred.away_spread}</div>
                      </div>
                    </div>
                  </div>

                  <div className="text-center p-6 rounded-xl bg-slate-900/80 border border-slate-700/50">
                    <div className={`text-5xl font-black mb-3 ${pred.prediction === pred.home_team ? 'text-blue-400' : 'text-slate-600'}`}>
                      {(pred.home_win_probability).toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Win Probability</div>
                    <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <div className="text-slate-500">Odds</div>
                        <div className="text-white font-mono">{pred.home_odds}</div>
                      </div>
                      <div>
                        <div className="text-slate-500">Spread</div>
                        <div className="text-white font-mono">{pred.home_spread > 0 ? '+' : ''}{pred.home_spread}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Prediction */}
                <div className={`rounded-xl p-6 mb-6 border-2 ${getConfidenceBg(pred.confidence)}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-slate-300 font-semibold uppercase tracking-wider">Predicted Winner:</span>
                    <span className="text-2xl font-black text-white">
                      {pred.prediction}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400 font-semibold">Ensemble Confidence:</span>
                    <div className="flex items-center gap-3">
                      <div className="w-40 h-4 bg-slate-900 rounded-full overflow-hidden border border-slate-700">
                        <div
                          className={`h-full ${pred.confidence >= 70 ? 'bg-green-500' :
                              pred.confidence >= 60 ? 'bg-yellow-500' :
                                'bg-orange-500'
                            }`}
                          style={{ width: `${Math.min(pred.confidence, 100)}%` }}
                        />
                      </div>
                      <span className={`text-lg font-black ${getConfidenceColor(pred.confidence)}`}>
                        {pred.confidence.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && predictions.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No predictions available</p>
            <p className="text-sm text-gray-500 mt-2">Check that the API server is running and try refreshing</p>
          </div>
        )}
      </div>
    </div>
  )
}
