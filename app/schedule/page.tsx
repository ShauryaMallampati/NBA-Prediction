"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card } from "@/components/ui/card"

const mockGames = [
  {
    id: "1",
    date: "2025-10-27",
    time: "7:30 PM ET",
    homeTeam: "Los Angeles Lakers",
    awayTeam: "Boston Celtics",
    homeWinProb: 0.4,
    awayWinProb: 0.6,
    homeElo: 1620,
    awayElo: 1650,
    homeRecord: "25-15",
    awayRecord: "28-12",
    confidence: "medium",
  },
  {
    id: "2",
    date: "2025-10-27",
    time: "8:00 PM ET",
    homeTeam: "Golden State Warriors",
    awayTeam: "Milwaukee Bucks",
    homeWinProb: 0.55,
    awayWinProb: 0.45,
    homeElo: 1640,
    awayElo: 1625,
    homeRecord: "27-13",
    awayRecord: "26-14",
    confidence: "high",
  },
  {
    id: "3",
    date: "2025-10-27",
    time: "9:30 PM ET",
    homeTeam: "Phoenix Suns",
    awayTeam: "Denver Nuggets",
    homeWinProb: 0.48,
    awayWinProb: 0.52,
    homeElo: 1630,
    awayElo: 1635,
    homeRecord: "26-14",
    awayRecord: "27-13",
    confidence: "low",
  },
]

export default function SchedulePage() {
  const [selectedDate, setSelectedDate] = useState("2025-10-27")

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
            <Link href="/schedule" className="text-sm font-semibold text-primary relative">
              Schedule
              <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary" />
            </Link>
            <Link href="/live" className="text-sm font-semibold hover:text-primary transition-colors">
              Live
            </Link>
            <Link href="/chemistry" className="text-sm font-semibold hover:text-primary transition-colors">
              Chemistry
            </Link>
            <Link href="/sentiment" className="text-sm font-semibold hover:text-primary transition-colors">
              Sentiment
            </Link>
            <Link href="/postgame" className="text-sm font-semibold hover:text-primary transition-colors">
              Analytics
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="mb-12">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Home</span>
          </Link>

          <div className="flex items-center gap-4 mb-6">
            <Calendar className="w-12 h-12 text-primary glow" />
            <div>
              <h1 className="text-6xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
                Game Schedule
              </h1>
              <p className="text-xl text-muted-foreground font-medium mt-2">ML-powered pregame analysis</p>
            </div>
          </div>
        </div>

        <Card className="p-8 mb-12 glass-strong border-2">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            <div className="flex-1">
              <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3 block">
                Select Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full md:w-auto px-6 py-4 rounded-xl border-2 border-border bg-background text-foreground font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="font-medium">High Confidence</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-secondary" />
                <span className="font-medium">Medium Confidence</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-muted-foreground" />
                <span className="font-medium">Low Confidence</span>
              </div>
            </div>
          </div>
        </Card>

        <div className="space-y-6">
          {mockGames.map((game) => (
            <Card
              key={game.id}
              className="p-8 glass-strong border-2 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      game.confidence === "high"
                        ? "bg-primary"
                        : game.confidence === "medium"
                          ? "bg-secondary"
                          : "bg-muted-foreground"
                    } glow`}
                  />
                  <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">{game.time}</span>
                </div>
                <span
                  className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${
                    game.confidence === "high"
                      ? "bg-primary/20 text-primary"
                      : game.confidence === "medium"
                        ? "bg-secondary/20 text-secondary"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {game.confidence} confidence
                </span>
              </div>

              <div className="grid md:grid-cols-3 gap-8 items-center">
                {/* Away Team */}
                <div className="text-center md:text-right space-y-3">
                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>
                    {game.awayTeam}
                  </h3>
                  <div className="flex items-center justify-center md:justify-end gap-4 text-sm text-muted-foreground">
                    <span className="font-semibold">{game.awayRecord}</span>
                    <span>•</span>
                    <span className="font-semibold">Elo: {game.awayElo}</span>
                  </div>
                  <div className="flex items-center justify-center md:justify-end gap-2">
                    <span className="text-5xl font-black text-primary">{(game.awayWinProb * 100).toFixed(0)}%</span>
                    {game.awayWinProb > 0.5 ? (
                      <TrendingUp className="w-8 h-8 text-primary" />
                    ) : game.awayWinProb < 0.5 ? (
                      <TrendingDown className="w-8 h-8 text-muted-foreground" />
                    ) : (
                      <Minus className="w-8 h-8 text-muted-foreground" />
                    )}
                  </div>
                </div>

                {/* VS Divider */}
                <div className="flex flex-col items-center justify-center">
                  <div
                    className="text-4xl font-black text-muted-foreground mb-4"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    VS
                  </div>
                  <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500"
                      style={{ width: `${game.awayWinProb * 100}%` }}
                    />
                  </div>
                  <div className="mt-4 text-sm text-muted-foreground font-semibold">
                    Predicted Spread: {game.awayWinProb > game.homeWinProb ? "Away" : "Home"} by{" "}
                    {Math.abs((game.awayWinProb - game.homeWinProb) * 20).toFixed(1)}
                  </div>
                </div>

                {/* Home Team */}
                <div className="text-center md:text-left space-y-3">
                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>
                    {game.homeTeam}
                  </h3>
                  <div className="flex items-center justify-center md:justify-start gap-4 text-sm text-muted-foreground">
                    <span className="font-semibold">{game.homeRecord}</span>
                    <span>•</span>
                    <span className="font-semibold">Elo: {game.homeElo}</span>
                  </div>
                  <div className="flex items-center justify-center md:justify-start gap-2">
                    {game.homeWinProb > 0.5 ? (
                      <TrendingUp className="w-8 h-8 text-primary" />
                    ) : game.homeWinProb < 0.5 ? (
                      <TrendingDown className="w-8 h-8 text-muted-foreground" />
                    ) : (
                      <Minus className="w-8 h-8 text-muted-foreground" />
                    )}
                    <span className="text-5xl font-black text-primary">{(game.homeWinProb * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              {/* Key Factors */}
              <div className="mt-8 pt-8 border-t border-border">
                <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Key Factors</h4>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    <span className="text-muted-foreground">
                      Home advantage: <span className="font-bold text-foreground">+3.2%</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-secondary" />
                    <span className="text-muted-foreground">
                      Recent form: <span className="font-bold text-foreground">+2.1%</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-chart-3" />
                    <span className="text-muted-foreground">
                      Rest differential: <span className="font-bold text-foreground">+1.5%</span>
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}
