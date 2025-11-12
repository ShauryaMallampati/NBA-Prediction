"use client"

import { AlertCircle, Calendar, RefreshCw, TrendingUp, ArrowLeft, Brain, Target } from "lucide-react"
import { useEffect, useState } from "react"
import Link from "next/link"

interface Prediction {
  game_id: string
  date: string
  home_team: string
  away_team: string
  home_win_prob: number
  away_win_prob: number
  predicted_winner: string
  confidence: number
  top_feature_1: string | null
  top_feature_2: string | null
  top_feature_3: string | null
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )

  const fetchPredictions = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/predictions?date=${selectedDate}`)
      const data = await response.json()
      
      if (data.success) {
        setPredictions(data.predictions || [])
      } else {
        setError(data.message || "No predictions available")
        setPredictions([])
      }
    } catch (err) {
      setError("Failed to fetch predictions")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPredictions()
  }, [selectedDate])

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.70) return "text-green-400"
    if (confidence >= 0.60) return "text-yellow-400"
    return "text-orange-400"
  }

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.70) return "bg-green-500/20"
    if (confidence >= 0.60) return "bg-yellow-500/20"
    return "bg-orange-500/20"
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      {/* Navigation Bar */}
      <nav className="glass-strong border-b border-gray-800 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🏀
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tight">NBA Intel</h1>
                <p className="text-xs text-gray-400">ML-Powered Analytics</p>
              </div>
            </Link>
            
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-purple-400 transition-colors">
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </Link>
              <Link href="/schedule" className="text-sm text-gray-400 hover:text-purple-400 transition-colors">
                Schedule
              </Link>
              <Link href="/live" className="text-sm text-gray-400 hover:text-purple-400 transition-colors">
                Live
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
              <Target className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Game Predictions
              </h1>
              <p className="text-gray-400 text-lg">
                AI-powered predictions using ensemble machine learning
              </p>
            </div>
            
            <button
              onClick={fetchPredictions}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-xl transition-colors shadow-lg hover:shadow-purple-500/50"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 border border-purple-400/30">
              <Brain className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-purple-300 font-semibold">XGBoost + LightGBM + CatBoost</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 border border-green-400/30">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-300 font-semibold">81.0% Accuracy</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 border border-blue-400/30">
              <span className="text-sm text-blue-300 font-semibold">0.912 AUC</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-yellow-500/20 border border-yellow-400/30">
              <span className="text-sm text-yellow-300 font-semibold">63% CV Accuracy</span>
            </div>
          </div>
        </div>

        {/* Date Selector */}
        <div className="glass-strong rounded-xl p-4 mb-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-5 h-5 text-purple-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
            />
            <span className="text-sm text-gray-400">
              {predictions.length} predictions available
            </span>
          </div>
        </div>

        {/* Model Performance Stats */}
        {predictions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="glass-strong rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 mb-1">High Confidence</p>
                  <p className="text-2xl font-bold text-green-400">
                    {predictions.filter(p => p.confidence >= 0.65).length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">≥65% confidence</p>
            </div>

            <div className="glass-strong rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Medium Confidence</p>
                  <p className="text-2xl font-bold text-yellow-400">
                    {predictions.filter(p => p.confidence >= 0.55 && p.confidence < 0.65).length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-yellow-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">55-64% confidence</p>
            </div>

            <div className="glass-strong rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Close Games</p>
                  <p className="text-2xl font-bold text-orange-400">
                    {predictions.filter(p => p.confidence < 0.55).length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-orange-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">&lt;55% confidence</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="glass-strong rounded-xl p-6 mb-6 border border-red-500/50">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-400 font-medium">Unable to load predictions</p>
                <p className="text-sm text-gray-400 mt-1">{error}</p>
                <p className="text-xs text-gray-500 mt-2">
                  Run: <code className="bg-gray-800 px-2 py-1 rounded">poetry run python scripts/generate_todays_predictions.py</code>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading predictions...</p>
          </div>
        )}

        {/* Predictions Grid */}
        {!loading && predictions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {predictions.map((pred) => (
              <div
                key={pred.game_id}
                className="glass-strong rounded-2xl p-8 hover:shadow-xl hover:shadow-purple-500/20 transition-all border border-gray-800 hover:border-purple-500/50"
              >
                {/* Matchup */}
                <div className="flex items-center justify-between mb-6">
                  <div className="text-center flex-1">
                    <div className="text-3xl font-bold text-white mb-1">{pred.away_team}</div>
                    <div className="text-sm text-gray-500 uppercase tracking-wider">Away</div>
                  </div>
                  
                  <div className="px-6">
                    <div className="text-2xl font-bold text-gray-600">@</div>
                  </div>
                  
                  <div className="text-center flex-1">
                    <div className="text-3xl font-bold text-white mb-1">{pred.home_team}</div>
                    <div className="text-sm text-gray-500 uppercase tracking-wider">Home</div>
                  </div>
                </div>

                {/* Probabilities */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div className="text-center p-4 rounded-xl bg-gray-800/50">
                    <div className={`text-4xl font-bold mb-2 ${pred.predicted_winner === pred.away_team ? 'text-purple-400' : 'text-gray-600'}`}>
                      {(pred.away_win_prob * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 uppercase tracking-wider">Win Probability</div>
                  </div>
                  
                  <div className="text-center p-4 rounded-xl bg-gray-800/50">
                    <div className={`text-4xl font-bold mb-2 ${pred.predicted_winner === pred.home_team ? 'text-purple-400' : 'text-gray-600'}`}>
                      {(pred.home_win_prob * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 uppercase tracking-wider">Win Probability</div>
                  </div>
                </div>

                {/* Prediction */}
                <div className={`${getConfidenceBg(pred.confidence)} rounded-xl p-4 mb-6 border ${
                  pred.confidence >= 0.70 ? 'border-green-500/30' : 
                  pred.confidence >= 0.60 ? 'border-yellow-500/30' : 
                  'border-orange-500/30'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400 font-medium">Predicted Winner:</span>
                    <span className={`text-xl font-bold ${getConfidenceColor(pred.confidence)}`}>
                      {pred.predicted_winner}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Model Confidence:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${
                            pred.confidence >= 0.70 ? 'bg-green-500' : 
                            pred.confidence >= 0.60 ? 'bg-yellow-500' : 
                            'bg-orange-500'
                          }`}
                          style={{ width: `${pred.confidence * 100}%` }}
                        />
                      </div>
                      <span className={`text-sm font-bold ${getConfidenceColor(pred.confidence)}`}>
                        {(pred.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Factors */}
                {pred.top_feature_1 && (
                  <div className="border-t border-gray-800 pt-4">
                    <div className="flex items-start gap-3">
                      <TrendingUp className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-semibold">Key Factors:</p>
                        <div className="flex flex-wrap gap-2">
                          {[pred.top_feature_1, pred.top_feature_2, pred.top_feature_3]
                            .filter(Boolean)
                            .map((feature, idx) => (
                              <span
                                key={idx}
                                className="text-xs bg-gray-800 px-3 py-1.5 rounded-lg text-gray-300 border border-gray-700 font-medium"
                              >
                                {feature?.replace(/_/g, ' ')}
                              </span>
                            ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && predictions.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No predictions available for this date</p>
            <p className="text-sm text-gray-500 mt-2">Try selecting a different date or generate new predictions</p>
          </div>
        )}
      </div>
    </div>
  )
}
