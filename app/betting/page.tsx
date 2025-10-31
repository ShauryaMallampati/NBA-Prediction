"use client"

import { useState } from "react"
import Link from "next/link"
import {
  DollarSign,
  TrendingUp,
  Target,
  Calculator,
  PieChart,
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react"

interface BetRecommendation {
  stat: string
  player: string
  line: number
  prediction: "over" | "under"
  confidence: number
  edge: number
  kellyFraction: number
  recommendedBet: number
  maxBet: number
  expectedValue: number
}

export default function BettingPage() {
  const [bankroll, setBankroll] = useState(10000)
  const [kellyDivisor, setKellyDivisor] = useState(4) // 1/4 Kelly
  const [minEdge, setMinEdge] = useState(5)
  const [odds, setOdds] = useState(-110)

  // Mock recommendations
  const recommendations: BetRecommendation[] = [
    {
      stat: "PTS",
      player: "LeBron James",
      line: 25.5,
      prediction: "over",
      confidence: 0.73,
      edge: 23.0,
      kellyFraction: 0.092,
      recommendedBet: 230,
      maxBet: 920,
      expectedValue: 52.9
    },
    {
      stat: "AST",
      player: "Luka Doncic",
      line: 8.5,
      prediction: "over",
      confidence: 0.69,
      edge: 19.0,
      kellyFraction: 0.076,
      recommendedBet: 190,
      maxBet: 760,
      expectedValue: 36.1
    },
    {
      stat: "REB",
      player: "Anthony Davis",
      line: 11.5,
      prediction: "over",
      confidence: 0.71,
      edge: 21.0,
      kellyFraction: 0.084,
      recommendedBet: 210,
      maxBet: 840,
      expectedValue: 44.1
    },
    {
      stat: "PTS",
      player: "Stephen Curry",
      line: 28.5,
      prediction: "under",
      confidence: 0.67,
      edge: 17.0,
      kellyFraction: 0.068,
      recommendedBet: 170,
      maxBet: 680,
      expectedValue: 28.9
    },
    {
      stat: "AST",
      player: "Chris Paul",
      line: 7.5,
      prediction: "over",
      confidence: 0.65,
      edge: 15.0,
      kellyFraction: 0.060,
      recommendedBet: 150,
      maxBet: 600,
      expectedValue: 22.5
    }
  ]

  const totalRecommendedBets = recommendations.reduce((sum, r) => sum + r.recommendedBet, 0)
  const totalExpectedValue = recommendations.reduce((sum, r) => sum + r.expectedValue, 0)
  const avgEdge = recommendations.reduce((sum, r) => sum + r.edge, 0) / recommendations.length

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
              <p className="text-xs text-muted-foreground font-medium">Betting Strategy</p>
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
        {/* Kelly Criterion Settings */}
        <div className="max-w-6xl mx-auto mb-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <Calculator className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Kelly Criterion Settings</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Bankroll ($)</label>
              <input
                type="number"
                value={bankroll}
                onChange={(e) => setBankroll(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold text-lg"
                min="0"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Kelly Divisor</label>
              <select
                value={kellyDivisor}
                onChange={(e) => setKellyDivisor(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold"
              >
                <option value="1">Full Kelly (1)</option>
                <option value="2">Half Kelly (1/2)</option>
                <option value="4">Quarter Kelly (1/4)</option>
                <option value="8">Eighth Kelly (1/8)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Min Edge (%)</label>
              <input
                type="number"
                value={minEdge}
                onChange={(e) => setMinEdge(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold"
                min="0"
                max="100"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Odds</label>
              <input
                type="number"
                value={odds}
                onChange={(e) => setOdds(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-background border-2 border-border hover:border-primary/50 focus:border-primary focus:outline-none transition-colors font-bold"
              />
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-6 p-4 rounded-xl bg-chart-4/10 border-2 border-chart-4/20 flex items-start gap-3">
            <Info className="w-5 h-5 text-chart-4 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-bold text-foreground mb-1">Kelly Criterion Strategy</p>
              <p>
                Optimal bet sizing based on edge and confidence. Using 1/{kellyDivisor} Kelly for conservative 
                bankroll management. Only showing picks with {minEdge}%+ edge.
              </p>
            </div>
          </div>
        </div>

        {/* Portfolio Summary */}
        <div className="max-w-6xl mx-auto mb-12 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10">
            <div className="flex items-center justify-between mb-3">
              <DollarSign className="w-8 h-8 text-chart-5" />
              <TrendingUp className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Total Allocation</p>
            <p className="text-3xl font-black text-chart-5" style={{ fontFamily: "var(--font-display)" }}>
              ${totalRecommendedBets}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {((totalRecommendedBets / bankroll) * 100).toFixed(1)}% of bankroll
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10">
            <div className="flex items-center justify-between mb-3">
              <Target className="w-8 h-8 text-primary" />
              <CheckCircle2 className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Total Picks</p>
            <p className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>
              {recommendations.length}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {recommendations.filter(r => r.prediction === "over").length} OVER / {recommendations.filter(r => r.prediction === "under").length} UNDER
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10">
            <div className="flex items-center justify-between mb-3">
              <PieChart className="w-8 h-8 text-chart-2" />
              <TrendingUp className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Avg Edge</p>
            <p className="text-3xl font-black text-chart-2" style={{ fontFamily: "var(--font-display)" }}>
              {avgEdge.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Above {minEdge}% threshold
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp className="w-8 h-8 text-chart-5" />
              <CheckCircle2 className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Expected Value</p>
            <p className="text-3xl font-black text-chart-5" style={{ fontFamily: "var(--font-display)" }}>
              +${totalExpectedValue.toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              +{((totalExpectedValue / totalRecommendedBets) * 100).toFixed(1)}% ROI
            </p>
          </div>
        </div>

        {/* Recommendations Table */}
        <div className="max-w-6xl mx-auto p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <Target className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Top Recommendations</h2>
          </div>

          <div className="space-y-4">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center font-black text-xl">
                      #{idx + 1}
                    </div>
                    <div>
                      <h3 className="text-xl font-black">{rec.player}</h3>
                      <p className="text-sm text-muted-foreground">
                        {rec.stat} {rec.prediction === "over" ? "OVER" : "UNDER"} {rec.line}
                      </p>
                    </div>
                  </div>

                  <div
                    className={`px-6 py-3 rounded-xl font-bold text-lg flex items-center gap-2 ${
                      rec.edge >= 20
                        ? "bg-chart-5/20 text-chart-5"
                        : rec.edge >= 15
                        ? "bg-chart-4/20 text-chart-4"
                        : "bg-chart-2/20 text-chart-2"
                    }`}
                  >
                    <TrendingUp className="w-5 h-5" />
                    {rec.edge.toFixed(1)}% Edge
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                  <div className="p-3 rounded-lg bg-muted text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">Confidence</p>
                    <p className="font-black">{(rec.confidence * 100).toFixed(0)}%</p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">Kelly %</p>
                    <p className="font-black">{(rec.kellyFraction * 100).toFixed(1)}%</p>
                  </div>

                  <div className="p-3 rounded-lg bg-chart-5/20 border-2 border-chart-5/30 text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">Recommended</p>
                    <p className="font-black text-chart-5">${rec.recommendedBet}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">Max Bet</p>
                    <p className="font-black">${rec.maxBet}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-chart-5/20 border-2 border-chart-5/30 text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">EV</p>
                    <p className="font-black text-chart-5">+${rec.expectedValue.toFixed(1)}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted text-center">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">ROI</p>
                    <p className="font-black">+{((rec.expectedValue / rec.recommendedBet) * 100).toFixed(0)}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Warning */}
        <div className="max-w-6xl mx-auto mt-8 p-6 rounded-2xl bg-destructive/10 border-2 border-destructive/20 flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-destructive flex-shrink-0 mt-1" />
          <div className="text-sm text-muted-foreground">
            <p className="font-bold text-destructive mb-2">Risk Disclaimer</p>
            <p>
              These are ML-powered predictions for informational purposes only. Never bet more than you can afford to lose. 
              Past performance does not guarantee future results. Use fractional Kelly sizing for conservative bankroll management.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
