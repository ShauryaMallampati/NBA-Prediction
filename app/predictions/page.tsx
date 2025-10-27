"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  BarChart3,
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
} from "lucide-react"

interface StatPrediction {
  raw: number
  calibrated: number
  over: boolean
  confidence: number
}

interface PlayerPrediction {
  player_name: string
  predictions: {
    PTS: StatPrediction
    AST: StatPrediction
    REB: StatPrediction
    STL: StatPrediction
    BLK: StatPrediction
  }
  ready_for_production: boolean
  error: string | null
}

const statLabels = {
  PTS: "Points",
  AST: "Assists",
  REB: "Rebounds",
  STL: "Steals",
  BLK: "Blocks",
}

const statEmojis = {
  PTS: "🔥",
  AST: "🎯",
  REB: "💪",
  STL: "🛡️",
  BLK: "🚫",
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<PlayerPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [playerName, setPlayerName] = useState("LeBron James")
  const [team, setTeam] = useState("LAL")
  const [opponent, setOpponent] = useState("GSW")
  const [gameDate, setGameDate] = useState("2024-10-26")
  const [bankroll, setBankroll] = useState(10000)
  const [activeTab, setActiveTab] = useState("predictions")

  const fetchPredictions = async () => {
    setLoading(true)
    setError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

      const response = await fetch(`${backendUrl}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          player_name: playerName,
          game_date: gameDate,
          team: team,
          opponent: opponent,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setPredictions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch predictions")
      console.error("Error:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPredictions()
    const interval = setInterval(fetchPredictions, 30000)
    return () => clearInterval(interval)
  }, [])

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
          <button
            onClick={fetchPredictions}
            disabled={loading}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-all duration-300 glow-lg shadow-xl disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        {error && (
          <div className="max-w-4xl mx-auto mb-8 p-6 rounded-2xl bg-destructive/10 border-2 border-destructive/50 flex items-center gap-4">
            <AlertCircle className="w-6 h-6 text-destructive flex-shrink-0" />
            <div>
              <p className="font-bold text-destructive">Error loading predictions</p>
              <p className="text-sm text-destructive/80">{error}</p>
            </div>
          </div>
        )}

        <div className="max-w-4xl mx-auto mb-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <Brain className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Get Predictions</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Player</label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors"
                placeholder="Player name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Team</label>
              <input
                type="text"
                value={team}
                onChange={(e) => setTeam(e.target.value.toUpperCase())}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors"
                placeholder="LAL"
                maxLength={3}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Opponent</label>
              <input
                type="text"
                value={opponent}
                onChange={(e) => setOpponent(e.target.value.toUpperCase())}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors"
                placeholder="GSW"
                maxLength={3}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Date</label>
              <input
                type="date"
                value={gameDate}
                onChange={(e) => setGameDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Bankroll</label>
              <input
                type="number"
                value={bankroll}
                onChange={(e) => setBankroll(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors"
                placeholder="10000"
              />
            </div>
          </div>

          <button
            onClick={fetchPredictions}
            disabled={loading}
            className="w-full px-8 py-4 rounded-2xl bg-gradient-to-r from-primary to-secondary text-primary-foreground font-bold text-lg hover:scale-105 transition-all duration-300 glow-lg shadow-xl disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Get Predictions
              </>
            )}
          </button>
        </div>

        <div className="max-w-4xl mx-auto mb-8 flex gap-2 flex-wrap">
          {[
            { id: "predictions", label: "Predictions", icon: Target },
            { id: "kelly", label: "Betting", icon: DollarSign },
            { id: "stats", label: "Statistics", icon: BarChart3 },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300 ${
                activeTab === id
                  ? "bg-primary text-primary-foreground glow-lg"
                  : "glass-strong border-2 border-transparent hover:border-primary/50"
              }`}
            >
              <Icon className="w-5 h-5" />
              {label}
            </button>
          ))}
        </div>

        {loading && !predictions ? (
          <div className="flex justify-center items-center py-24">
            <div className="text-center space-y-4">
              <RefreshCw className="w-16 h-16 animate-spin text-primary mx-auto" />
              <p className="text-lg font-semibold">Analyzing player performance...</p>
            </div>
          </div>
        ) : predictions ? (
          <>
            {activeTab === "predictions" && (
              <div className="max-w-4xl mx-auto space-y-8">
                <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10">
                  <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                      <h1 className="text-4xl font-black mb-2">{predictions.player_name}</h1>
                      <p className="text-lg text-muted-foreground">
                        {team} vs {opponent} • {gameDate}
                      </p>
                    </div>
                    <div
                      className={`px-6 py-3 rounded-xl font-bold text-lg flex items-center gap-2 ${
                        predictions.ready_for_production
                          ? "bg-chart-5/20 text-chart-5"
                          : "bg-destructive/20 text-destructive"
                      }`}
                    >
                      {predictions.ready_for_production ? (
                        <>
                          <CheckCircle2 className="w-6 h-6" />
                          Ready
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-6 h-6" />
                          Caution
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                  {Object.entries(predictions.predictions).map(([stat, pred]) => {
                    const label = statLabels[stat as keyof typeof statLabels]
                    const emoji = statEmojis[stat as keyof typeof statEmojis]
                    const isOver = pred.over

                    return (
                      <div
                        key={stat}
                        className="group p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/50 transition-all duration-300 hover:scale-105"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="text-4xl">{emoji}</div>
                          {isOver ? (
                            <TrendingUp className="w-5 h-5 text-chart-5" />
                          ) : (
                            <TrendingDown className="w-5 h-5 text-destructive" />
                          )}
                        </div>

                        <p className="text-sm font-semibold text-muted-foreground mb-1">{label}</p>
                        <p className="text-3xl font-black mb-4" style={{ fontFamily: "var(--font-display)" }}>
                          {isOver ? "OVER" : "UNDER"}
                        </p>

                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-xs font-semibold text-muted-foreground">Confidence</span>
                              <span className="font-bold text-sm">{(pred.confidence * 100).toFixed(0)}%</span>
                            </div>
                            <div className="h-2 rounded-full bg-muted overflow-hidden">
                              <div
                                className={`h-full transition-all duration-300 ${
                                  isOver
                                    ? "bg-gradient-to-r from-chart-5 to-chart-5/50"
                                    : "bg-gradient-to-r from-destructive to-destructive/50"
                                }`}
                                style={{ width: `${pred.confidence * 100}%` }}
                              />
                            </div>
                          </div>

                          <div className="pt-3 border-t border-border">
                            <p className="text-xs text-muted-foreground font-semibold mb-1">Edge</p>
                            <p className="font-bold text-primary">
                              {((pred.confidence - 0.5) * 100).toFixed(1)}%
                            </p>
                          </div>

                          <div className="pt-3 border-t border-border space-y-2">
                            <div className="flex justify-between">
                              <span className="text-xs text-muted-foreground">Raw</span>
                              <span className="font-bold text-sm">{(pred.raw * 100).toFixed(1)}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-muted-foreground">Calibrated</span>
                              <span className="font-bold text-sm text-primary">{(pred.calibrated * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {activeTab === "kelly" && (
              <div className="max-w-4xl mx-auto p-8 rounded-3xl glass-strong border-2 border-primary/10">
                <h3 className="text-2xl font-black mb-6 flex items-center gap-3">
                  <DollarSign className="w-6 h-6 text-primary" />
                  Kelly Criterion Strategy
                </h3>
                <p className="text-center text-muted-foreground">
                  Bankroll: ${bankroll.toLocaleString()} | Kelly Fraction: 25% | Min Edge: 5%
                </p>
              </div>
            )}

            {activeTab === "stats" && (
              <div className="max-w-4xl mx-auto p-8 rounded-3xl glass-strong border-2 border-primary/10">
                <h3 className="text-2xl font-black mb-6 flex items-center gap-3">
                  <BarChart3 className="w-6 h-6 text-primary" />
                  Model Statistics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground font-semibold">Models Active</p>
                    <p className="font-bold">5</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground font-semibold">Feature Set</p>
                    <p className="font-bold">53</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground font-semibold">Calibration</p>
                    <p className="font-bold">Isotonic</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground font-semibold">Status</p>
                    <p className="font-bold text-chart-5">Healthy</p>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="max-w-4xl mx-auto p-12 rounded-3xl glass-strong border-2 border-primary/10 text-center">
            <p className="text-muted-foreground text-lg">Click "Get Predictions" to see results</p>
          </div>
        )}
      </main>
    </div>
  )
}
