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
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // Always default to today (2025-11-12 in PST)
    const today = new Date()
    today.setHours(today.getHours() - 8) // Adjust to PST
    return today.toISOString().split('T')[0]
  })

  const fetchPredictions = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/predictions?date=${selectedDate}`)
      const data = await response.json()
      
      if (data.success) {
        setPredictions(data.predictions || [])
        setError(null)
      } else {
        setError(data.message || "No predictions available for this date")
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
              <Link href="/schedule" className="text-sm text-slate-300 hover:text-blue-400 transition-colors">
                Schedule
              </Link>
              <Link href="/live" className="text-sm text-slate-300 hover:text-blue-400 transition-colors">
                Live
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
            AI-powered predictions using ensemble machine learning
          </p>
          
          <div className="flex flex-wrap justify-center gap-3 mb-6">
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-purple-600/30 border border-purple-400/50">
              <Brain className="w-5 h-5 text-purple-300" />
              <span className="text-sm text-white font-semibold">XGBoost + LightGBM + CatBoost</span>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-green-600/30 border border-green-400/50">
              <TrendingUp className="w-5 h-5 text-green-300" />
              <span className="text-sm text-white font-semibold">81.0% Accuracy</span>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600/30 border border-blue-400/50">
              <span className="text-sm text-white font-semibold">0.912 AUC</span>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-yellow-600/30 border border-yellow-400/50">
              <span className="text-sm text-white font-semibold">63% CV Accuracy</span>
            </div>
          </div>
            
          <button
            onClick={fetchPredictions}
            disabled={loading}
            className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-xl transition-all shadow-lg hover:shadow-blue-500/50 font-semibold"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Predictions
          </button>
        </div>

        {/* Date Selector */}
        <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 mb-8 border border-slate-700/50">
          <div className="flex items-center gap-4">
            <Calendar className="w-6 h-6 text-blue-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-6 py-3 bg-slate-900 text-white rounded-lg border-2 border-slate-700 focus:border-blue-500 focus:outline-none font-semibold text-lg"
            />
            <span className="text-lg text-slate-300 font-semibold">
              {predictions.length} predictions available
            </span>
          </div>
        </div>

        {/* Model Performance Stats */}
        {predictions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2 font-semibold">High Confidence</p>
                  <p className="text-4xl font-black text-green-400">
                    {predictions.filter(p => p.confidence >= 0.65).length}
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
                    {predictions.filter(p => p.confidence >= 0.55 && p.confidence < 0.65).length}
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
                    {predictions.filter(p => p.confidence < 0.55).length}
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
                <p className="text-yellow-400 font-bold text-xl mb-3">Predictions Not Yet Available</p>
                <p className="text-slate-300 text-lg mb-4">{error}</p>
                <div className="bg-slate-900/80 rounded-xl p-6 border border-slate-700/50">
                  <p className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-blue-400" />
                    Automated Prediction Schedule
                  </p>
                  <ul className="space-y-2 text-slate-300">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold">•</span>
                      <span>Predictions are automatically generated every day at <strong className="text-white">9:00 AM PST</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold">•</span>
                      <span>Predictions include all NBA games scheduled for that day</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold">•</span>
                      <span>Check back after 9 AM to see today's predictions</span>
                    </li>
                  </ul>
                </div>
                <div className="mt-6 flex items-center gap-4">
                  <button
                    onClick={fetchPredictions}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Retry
                  </button>
                  <Link
                    href="/schedule"
                    className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-semibold transition-all"
                  >
                    View Schedule
                  </Link>
                </div>
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
        {!loading && predictions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {predictions.map((pred) => (
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
                    <div className={`text-5xl font-black mb-3 ${pred.predicted_winner === pred.away_team ? 'text-blue-400' : 'text-slate-600'}`}>
                      {(pred.away_win_prob * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Win Probability</div>
                  </div>
                  
                  <div className="text-center p-6 rounded-xl bg-slate-900/80 border border-slate-700/50">
                    <div className={`text-5xl font-black mb-3 ${pred.predicted_winner === pred.home_team ? 'text-blue-400' : 'text-slate-600'}`}>
                      {(pred.home_win_prob * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Win Probability</div>
                  </div>
                </div>

                {/* Prediction */}
                <div className={`rounded-xl p-6 mb-6 border-2 ${
                  pred.confidence >= 0.70 ? 'bg-green-600/20 border-green-400/50' : 
                  pred.confidence >= 0.60 ? 'bg-yellow-600/20 border-yellow-400/50' : 
                  'bg-orange-600/20 border-orange-400/50'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-slate-300 font-semibold uppercase tracking-wider">Predicted Winner:</span>
                    <span className="text-2xl font-black text-white">
                      {pred.predicted_winner}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400 font-semibold">Model Confidence:</span>
                    <div className="flex items-center gap-3">
                      <div className="w-40 h-4 bg-slate-900 rounded-full overflow-hidden border border-slate-700">
                        <div 
                          className={`h-full ${
                            pred.confidence >= 0.70 ? 'bg-green-500' : 
                            pred.confidence >= 0.60 ? 'bg-yellow-500' : 
                            'bg-orange-500'
                          }`}
                          style={{ width: `${pred.confidence * 100}%` }}
                        />
                      </div>
                      <span className={`text-lg font-black ${
                        pred.confidence >= 0.70 ? 'text-green-400' : 
                        pred.confidence >= 0.60 ? 'text-yellow-400' : 
                        'text-orange-400'
                      }`}>
                        {(pred.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Factors */}
                {pred.top_feature_1 && (
                  <div className="border-t border-slate-700/50 pt-6">
                    <div className="flex items-start gap-3">
                      <TrendingUp className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-slate-300 mb-3 uppercase tracking-wider font-bold">Key Factors:</p>
                        <div className="flex flex-wrap gap-2">
                          {[pred.top_feature_1, pred.top_feature_2, pred.top_feature_3]
                            .filter(Boolean)
                            .map((feature, idx) => (
                              <span
                                key={idx}
                                className="text-sm bg-slate-900 px-4 py-2 rounded-lg text-white border border-slate-700 font-semibold"
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
