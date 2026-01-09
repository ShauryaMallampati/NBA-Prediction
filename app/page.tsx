"use client"

import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  Calendar,
  CheckCircle,
  MessageSquare,
  RefreshCw,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react"
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
}

interface PredictionsResponse {
  timestamp: string
  total_games: number
  predictions: EnsemblePrediction[]
}

export default function HomePage() {
  const [predictions, setPredictions] = useState<EnsemblePrediction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await fetch('http://localhost:8000/predictions')
        if (response.ok) {
          const data: PredictionsResponse = await response.json()
          setPredictions(data.predictions.slice(0, 6)) // Show first 6 games
        }
      } catch (error) {
        console.error('Failed to fetch predictions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPredictions()
    const interval = setInterval(fetchPredictions, 5 * 60 * 1000) // Refresh every 5 min
    return () => clearInterval(interval)
  }, [])

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
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">
      <header className="glass-strong sticky top-0 z-50 border-b">
        <div className="container mx-auto px-6 py-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow-lg group-hover:scale-110 transition-transform duration-300">
              🏀
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
                NBA Intel
              </h1>
              <p className="text-xs text-muted-foreground font-medium">ML-Powered Analytics</p>
            </div>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href="/ensemble-predictions"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Predictions
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/betting"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Betting
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/analytics"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Analytics
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/schedule"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Schedule
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/postgame"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Postgame
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/chemistry"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Chemistry
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/sentiment"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Sentiment
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6">
        <div className="max-w-7xl mx-auto text-center py-24 md:py-32 space-y-10">
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full glass-strong border-2 border-primary/20 text-sm font-bold mb-6 animate-pulse-slow">
            <Brain className="w-5 h-5 text-primary" />
            <span>Powered by Advanced Machine Learning</span>
          </div>

          <h2
            className="text-7xl md:text-9xl font-black text-balance leading-[0.9] tracking-tighter"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Predict Every
            <br />
            <span className="text-gradient">NBA Game</span>
          </h2>

          <p className="text-xl md:text-3xl text-muted-foreground text-pretty max-w-4xl mx-auto leading-relaxed font-medium">
            Real-time predictions, live win probability, player chemistry networks, and social sentiment analysis—all
            powered by cutting-edge AI
          </p>

          <div className="flex flex-wrap items-center justify-center gap-6 pt-8">
            <Link
              href="/ensemble-predictions"
              className="group inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-lg hover:scale-105 transition-all duration-300 glow-lg shadow-2xl hover:shadow-purple-500/50"
            >
              <Target className="w-6 h-6" />
              View All Predictions
              <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </Link>
            <Link
              href="/schedule"
              className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl glass-strong font-bold text-lg hover:bg-accent hover:scale-105 transition-all duration-300 border-2"
            >
              <Calendar className="w-5 h-5" />
              Schedule
            </Link>
            <Link
              href="/postgame"
              className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl glass-strong font-bold text-lg hover:bg-accent hover:scale-105 transition-all duration-300 border-2"
            >
              <BarChart3 className="w-5 h-5" />
              Postgame
            </Link>
          </div>
        </div>

        {/* Live Ensemble Predictions Section */}
        <div className="max-w-7xl mx-auto mb-24">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full glass-strong border-2 border-green-500/30 text-sm font-bold mb-6">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-green-400">Live Ensemble Predictions</span>
            </div>
            <h3 className="text-5xl md:text-6xl font-black mb-4" style={{ fontFamily: "var(--font-display)" }}>
              <span className="text-gradient">Today's Games</span>
            </h3>
            <p className="text-xl text-muted-foreground">6 ML models voting together for maximum accuracy</p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading predictions...</p>
            </div>
          ) : predictions.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {predictions.map((pred) => (
                <div
                  key={pred.game_id}
                  className="group p-6 rounded-2xl glass-strong hover:bg-accent/50 transition-all duration-300 hover:scale-[1.02] border-2 hover:border-primary/30 hover:shadow-xl"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-xs text-muted-foreground font-medium">
                      {formatTime(pred.commence_time)}
                    </div>
                    <div className={`px-3 py-1 rounded-lg text-xs font-bold ${pred.confidence >= 70
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : pred.confidence >= 50
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                      }`}>
                      {pred.confidence.toFixed(0)}% Confident
                    </div>
                  </div>

                  <div className="space-y-3 mb-4">
                    <div className={`p-3 rounded-lg border-2 ${pred.prediction === 'HOME_WIN'
                      ? 'bg-green-500/10 border-green-500/30'
                      : 'bg-slate-800/30 border-slate-700/30'
                      }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">HOME</div>
                          <div className="font-bold">{pred.home_team}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-black ${pred.prediction === 'HOME_WIN' ? 'text-green-400' : 'text-gray-500'
                            }`}>
                            {pred.home_win_probability.toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      {pred.prediction === 'HOME_WIN' && (
                        <div className="flex items-center gap-1 text-green-400 text-xs mt-2">
                          <CheckCircle className="w-3 h-3" />
                          <span className="font-semibold">Predicted Winner</span>
                        </div>
                      )}
                    </div>

                    <div className="text-center py-1">
                      <div className="text-xs text-muted-foreground font-bold">VS</div>
                    </div>

                    <div className={`p-3 rounded-lg border-2 ${pred.prediction === 'AWAY_WIN'
                      ? 'bg-green-500/10 border-green-500/30'
                      : 'bg-slate-800/30 border-slate-700/30'
                      }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">AWAY</div>
                          <div className="font-bold">{pred.away_team}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-black ${pred.prediction === 'AWAY_WIN' ? 'text-green-400' : 'text-gray-500'
                            }`}>
                            {pred.away_win_probability.toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      {pred.prediction === 'AWAY_WIN' && (
                        <div className="flex items-center gap-1 text-green-400 text-xs mt-2">
                          <CheckCircle className="w-3 h-3" />
                          <span className="font-semibold">Predicted Winner</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Model Agreement</span>
                      <span className="font-bold text-primary">{pred.models_agree}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 glass-strong rounded-2xl border-2">
              <Brain className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground mb-2">No predictions available</p>
              <p className="text-sm text-muted-foreground">Make sure the API server is running</p>
            </div>
          )}

          {predictions.length > 0 && (
            <div className="text-center">
              <Link
                href="/ensemble-predictions"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary font-bold transition-all hover:scale-105"
              >
                View All {predictions.length > 6 ? 'Predictions' : `${predictions.length} Games`}
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          )}
        </div>

        <div className="max-w-7xl mx-auto grid md:grid-cols-6 gap-6 mb-24">
          <Link
            href="/ensemble-predictions"
            className="group md:col-span-6 p-12 rounded-3xl bg-gradient-to-br from-purple-600/20 via-pink-600/20 to-purple-600/20 hover:from-purple-600/30 hover:via-pink-600/30 hover:to-purple-600/30 transition-all duration-500 hover:scale-[1.02] border-2 border-purple-500/50 hover:border-purple-400 hover:shadow-2xl hover:shadow-purple-500/30"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-purple-500/20 border border-purple-400/50 mb-6">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <span className="text-sm font-bold text-purple-300">Ensemble Models + XAI</span>
                </div>
                <h3 className="text-6xl font-black mb-6 text-balance bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent" style={{ fontFamily: "var(--font-display)" }}>
                  Advanced Predictions
                </h3>
                <p className="text-xl text-gray-300 leading-relaxed mb-8 max-w-3xl">
                  <span className="text-green-400 font-bold">XGBoost + LightGBM + CatBoost</span> ensemble.
                  Now with **Explainable AI (SHAP)** and **AI-Generated Scouting Reports** for every single game.
                </p>
                <div className="flex flex-wrap gap-4 mb-8">
                  <div className="px-4 py-2 rounded-lg bg-green-500/20 border border-green-400/30">
                    <span className="text-green-400 font-bold text-sm">67.7% Accuracy</span>
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-blue-500/20 border border-blue-400/30">
                    <span className="text-blue-400 font-bold text-sm">XAI Interpretability</span>
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-yellow-500/20 border border-yellow-400/30">
                    <span className="text-yellow-400 font-bold text-sm">Daily Automation</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-purple-400 font-bold text-lg">
                  Explore Modern Interface
                  <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
                </div>
              </div>
              <Target className="w-24 h-24 text-purple-400 opacity-50 group-hover:opacity-100 group-hover:scale-110 transition-all glow" />
            </div>
          </Link>

          <Link
            href="/ensemble-predictions"
            className="group md:col-span-4 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/20"
          >
            <Calendar className="w-16 h-16 text-primary mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Daily Runner
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-2xl">
              Automated script that fetches results every morning and tracks model performance against real outcomes.
            </p>
            <div className="flex items-center gap-3 text-primary font-bold text-lg">
              Check Track Record
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/postgame"
            className="group md:col-span-2 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-secondary/50 hover:shadow-2xl hover:shadow-secondary/20"
          >
            <TrendingUp className="w-16 h-16 text-secondary mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-4xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Accuracy Dashboard
            </h3>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Track our model's performance with real accuracy metrics and calibration analysis
            </p>
            <div className="flex items-center gap-3 text-secondary font-bold">
              View Stats
              <ArrowRight className="w-5 h-5 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/chemistry"
            className="group md:col-span-2 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-3/50 hover:shadow-2xl hover:shadow-chart-3/20"
          >
            <Users className="w-16 h-16 text-chart-3 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-4xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Player Chemistry
            </h3>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Graph Neural Network analysis of player synergies and lineup effectiveness
            </p>
            <div className="flex items-center gap-3 text-chart-3 font-bold">
              Analyze Chemistry
              <ArrowRight className="w-5 h-5 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/sentiment"
            className="group md:col-span-4 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-4/50 hover:shadow-2xl hover:shadow-chart-4/20"
          >
            <MessageSquare className="w-16 h-16 text-chart-4 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Social Sentiment Analysis
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-3xl">
              Track social media buzz and sentiment from Twitter, Reddit, and YouTube using transformer models
            </p>
            <div className="flex items-center gap-3 text-chart-4 font-bold text-lg">
              View Sentiment
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/postgame"
            className="group md:col-span-6 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-5/50 hover:shadow-2xl hover:shadow-chart-5/20"
          >
            <BarChart3 className="w-16 h-16 text-chart-5 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Postgame Analysis & Model Performance
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-4xl">
              Comprehensive model evaluation with calibration curves, SHAP explanations, and performance metrics
            </p>
            <div className="flex items-center gap-3 text-chart-5 font-bold text-lg">
              View Analytics
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>
        </div>

        <div className="max-w-7xl mx-auto mb-32">
          <div className="text-center mb-20">
            <h3 className="text-6xl font-black mb-6" style={{ fontFamily: "var(--font-display)" }}>
              Platform Capabilities
            </h3>
            <p className="text-2xl text-muted-foreground font-medium">
              Advanced ML models and real-time data processing
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Target,
                title: "Pregame Predictions",
                desc: "Elo + LightGBM ensemble with 70%+ accuracy",
                color: "text-primary",
              },
              {
                icon: Activity,
                title: "Live Win Probability",
                desc: "GRU sequences for possession-level updates",
                color: "text-secondary",
              },
              {
                icon: Zap,
                title: "Video Analysis",
                desc: "ResNet3D for highlight and foul detection",
                color: "text-chart-3",
              },
              {
                icon: Users,
                title: "Player Chemistry",
                desc: "Graph Neural Networks for lineup synergy",
                color: "text-chart-4",
              },
              {
                icon: MessageSquare,
                title: "Social Sentiment",
                desc: "DistilBERT transformers for text analysis",
                color: "text-chart-5",
              },
              {
                icon: Brain,
                title: "Model Explainability",
                desc: "SHAP values for prediction interpretation",
                color: "text-primary",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group p-10 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-300 hover:scale-105 border-2 hover:border-primary/30 hover:shadow-xl"
              >
                <feature.icon
                  className={`w-14 h-14 ${feature.color} mb-6 group-hover:scale-110 transition-transform glow`}
                />
                <h4 className="text-2xl font-bold mb-3" style={{ fontFamily: "var(--font-display)" }}>
                  {feature.title}
                </h4>
                <p className="text-muted-foreground leading-relaxed text-lg">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t glass-strong mt-32">
        <div className="container mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow">
                🏀
              </div>
              <div>
                <p className="font-black text-lg" style={{ fontFamily: "var(--font-display)" }}>
                  NBA Intelligence Platform
                </p>
                <p className="text-sm text-muted-foreground font-medium">Research Use Only • v0.1.0</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground font-medium">Powered by Next.js, FastAPI, PyTorch & LightGBM</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
