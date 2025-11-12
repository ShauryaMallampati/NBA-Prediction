"use client"

import {
    Activity,
    ArrowRight,
    BarChart3,
    Target,
    Users
} from "lucide-react"
import Link from "next/link"
import { useState } from "react"

interface PlayerStats {
  name: string
  team: string
  pts: number
  ast: number
  reb: number
  stl: number
  blk: number
  fg_pct: number
  three_pct: number
  usage: number
  confidence: number
}

export default function ComparePage() {
  const [player1, setPlayer1] = useState("LeBron James")
  const [player2, setPlayer2] = useState("Stephen Curry")
  
  // Mock data
  const player1Stats: PlayerStats = {
    name: "LeBron James",
    team: "LAL",
    pts: 25.7,
    ast: 7.3,
    reb: 8.3,
    stl: 1.3,
    blk: 0.7,
    fg_pct: 50.3,
    three_pct: 35.4,
    usage: 29.1,
    confidence: 0.73
  }

  const player2Stats: PlayerStats = {
    name: "Stephen Curry",
    team: "GSW",
    pts: 29.4,
    ast: 6.5,
    reb: 5.2,
    stl: 1.4,
    blk: 0.3,
    fg_pct: 48.2,
    three_pct: 41.3,
    usage: 32.4,
    confidence: 0.69
  }

  const stats = [
    { key: "pts", label: "Points", emoji: "🔥" },
    { key: "ast", label: "Assists", emoji: "🎯" },
    { key: "reb", label: "Rebounds", emoji: "💪" },
    { key: "stl", label: "Steals", emoji: "🛡️" },
    { key: "blk", label: "Blocks", emoji: "🚫" },
    { key: "fg_pct", label: "FG%", emoji: "🎪" },
    { key: "three_pct", label: "3P%", emoji: "🏹" },
    { key: "usage", label: "Usage", emoji: "⚡" },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">
      {/* Header */}
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
              <p className="text-xs text-muted-foreground font-medium">Player Comparison</p>
            </div>
          </Link>
          <Link
            href="/predictions"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-all duration-300 glow-lg shadow-xl"
          >
            <Target className="w-5 h-5" />
            Predictions
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        {/* Player Selection */}
        <div className="max-w-4xl mx-auto mb-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <Users className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Select Players to Compare</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Player 1</label>
              <input
                type="text"
                value={player1}
                onChange={(e) => setPlayer1(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold text-lg"
                placeholder="Player name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Player 2</label>
              <input
                type="text"
                value={player2}
                onChange={(e) => setPlayer2(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold text-lg"
                placeholder="Player name"
              />
            </div>
          </div>
        </div>

        {/* Comparison Header */}
        <div className="max-w-6xl mx-auto mb-8">
          <div className="grid grid-cols-3 gap-6">
            <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10 text-center">
              <div className="w-24 h-24 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-chart-1 to-chart-2 flex items-center justify-center text-4xl font-black">
                {player1Stats.team}
              </div>
              <h3 className="text-2xl font-black mb-2">{player1Stats.name}</h3>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-chart-5/20 text-chart-5 font-bold">
                <Target className="w-4 h-4" />
                {(player1Stats.confidence * 100).toFixed(0)}% Confidence
              </div>
            </div>

            <div className="flex items-center justify-center">
              <div className="p-6 rounded-2xl glass-strong border-2 border-primary/20">
                <ArrowRight className="w-8 h-8 text-primary" />
              </div>
            </div>

            <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10 text-center">
              <div className="w-24 h-24 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-chart-3 to-chart-4 flex items-center justify-center text-4xl font-black">
                {player2Stats.team}
              </div>
              <h3 className="text-2xl font-black mb-2">{player2Stats.name}</h3>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-chart-5/20 text-chart-5 font-bold">
                <Target className="w-4 h-4" />
                {(player2Stats.confidence * 100).toFixed(0)}% Confidence
              </div>
            </div>
          </div>
        </div>

        {/* Stats Comparison */}
        <div className="max-w-6xl mx-auto space-y-4">
          {stats.map(({ key, label, emoji }) => {
            const p1Val = player1Stats[key as keyof PlayerStats] as number
            const p2Val = player2Stats[key as keyof PlayerStats] as number
            const maxVal = Math.max(p1Val, p2Val)
            const p1Width = (p1Val / maxVal) * 100
            const p2Width = (p2Val / maxVal) * 100
            const winner = p1Val > p2Val ? "p1" : p2Val > p1Val ? "p2" : "tie"

            return (
              <div key={key} className="p-6 rounded-2xl glass-strong border-2 border-primary/10">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{emoji}</span>
                    <span className="font-bold text-lg">{label}</span>
                  </div>
                  {winner === "tie" ? (
                    <Activity className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <div className="text-sm font-bold text-muted-foreground">
                      {winner === "p1" ? "→ " + player1Stats.name : player2Stats.name + " ←"}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-muted-foreground">{player1Stats.name}</span>
                      <span className="font-black text-lg">{p1Val.toFixed(1)}</span>
                    </div>
                    <div className="h-4 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          winner === "p1"
                            ? "bg-gradient-to-r from-chart-5 to-chart-5/50"
                            : "bg-gradient-to-r from-chart-1 to-chart-1/50"
                        }`}
                        style={{ width: `${p1Width}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-muted-foreground">{player2Stats.name}</span>
                      <span className="font-black text-lg">{p2Val.toFixed(1)}</span>
                    </div>
                    <div className="h-4 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          winner === "p2"
                            ? "bg-gradient-to-r from-chart-5 to-chart-5/50"
                            : "bg-gradient-to-r from-chart-3 to-chart-3/50"
                        }`}
                        style={{ width: `${p2Width}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary */}
        <div className="max-w-6xl mx-auto mt-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="w-6 h-6 text-primary" />
            <h3 className="text-2xl font-bold">Head-to-Head Summary</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-chart-1/10 border-2 border-chart-1/20 text-center">
              <p className="text-sm text-muted-foreground font-semibold mb-2">{player1Stats.name} Advantages</p>
              <p className="text-5xl font-black text-chart-1" style={{ fontFamily: "var(--font-display)" }}>
                {stats.filter(s => (player1Stats[s.key as keyof PlayerStats] as number) > (player2Stats[s.key as keyof PlayerStats] as number)).length}
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-muted border-2 border-border text-center">
              <p className="text-sm text-muted-foreground font-semibold mb-2">Even Stats</p>
              <p className="text-5xl font-black" style={{ fontFamily: "var(--font-display)" }}>
                {stats.filter(s => (player1Stats[s.key as keyof PlayerStats] as number) === (player2Stats[s.key as keyof PlayerStats] as number)).length}
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-chart-3/10 border-2 border-chart-3/20 text-center">
              <p className="text-sm text-muted-foreground font-semibold mb-2">{player2Stats.name} Advantages</p>
              <p className="text-5xl font-black text-chart-3" style={{ fontFamily: "var(--font-display)" }}>
                {stats.filter(s => (player2Stats[s.key as keyof PlayerStats] as number) > (player1Stats[s.key as keyof PlayerStats] as number)).length}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
