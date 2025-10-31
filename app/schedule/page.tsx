"use client""use client"



import { useEffect, useState } from "react"import { useState } from "react"

import { Calendar, ChevronLeft, ChevronRight, RefreshCw, AlertCircle } from "lucide-react"import Link from "next/link"

import Link from "next/link"import { ArrowLeft, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react"

import { Card } from "@/components/ui/card"

interface Team {

  id: numberconst mockGames = [

  name: string  {

  abbreviation: string    id: "1",

  score: number    date: "2025-10-27",

}    time: "7:30 PM ET",

    homeTeam: "Los Angeles Lakers",

interface Game {    awayTeam: "Boston Celtics",

  game_id: string    homeWinProb: 0.4,

  date: string    awayWinProb: 0.6,

  status: string    homeElo: 1620,

  home_team: Team    awayElo: 1650,

  visitor_team: Team    homeRecord: "25-15",

}    awayRecord: "28-12",

    confidence: "medium",

interface GamesResponse {  },

  success: boolean  {

  count: number    id: "2",

  games: Game[]    date: "2025-10-27",

}    time: "8:00 PM ET",

    homeTeam: "Golden State Warriors",

export default function SchedulePage() {    awayTeam: "Milwaukee Bucks",

  const [games, setGames] = useState<Game[]>([])    homeWinProb: 0.55,

  const [loading, setLoading] = useState(true)    awayWinProb: 0.45,

  const [error, setError] = useState<string | null>(null)    homeElo: 1640,

  const [currentDate, setCurrentDate] = useState<Date>(new Date())    awayElo: 1625,

    homeRecord: "27-13",

  const fetchGames = async (date: Date) => {    awayRecord: "26-14",

    setLoading(true)    confidence: "high",

    setError(null)  },

  {

    try {    id: "3",

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"    date: "2025-10-27",

      const dateStr = date.toISOString().split('T')[0]    time: "9:30 PM ET",

      const response = await fetch(`${backendUrl}/api/games?date=${dateStr}`)    homeTeam: "Phoenix Suns",

    awayTeam: "Denver Nuggets",

      if (!response.ok) {    homeWinProb: 0.48,

        throw new Error(`HTTP error! status: ${response.status}`)    awayWinProb: 0.52,

      }    homeElo: 1630,

    awayElo: 1635,

      const data: GamesResponse = await response.json()    homeRecord: "26-14",

      setGames(data.games || [])    awayRecord: "27-13",

    } catch (err) {    confidence: "low",

      setError(err instanceof Error ? err.message : "Failed to fetch games")  },

      console.error("Error:", err)]

    } finally {

      setLoading(false)export default function SchedulePage() {

    }  const [selectedDate, setSelectedDate] = useState("2025-10-27")

  }

  return (

  useEffect(() => {    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">

    fetchGames(currentDate)      <header className="glass-strong sticky top-0 z-50 border-b">

  }, [currentDate])        <div className="container mx-auto px-6 py-6 flex items-center justify-between">

          <Link href="/" className="flex items-center gap-3 group">

  const goToPreviousDay = () => {            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow-lg group-hover:scale-110 transition-transform duration-300">

    const prevDay = new Date(currentDate)              🏀

    prevDay.setDate(prevDay.getDate() - 1)            </div>

    setCurrentDate(prevDay)            <div>

  }              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

                NBA Intel

  const goToNextDay = () => {              </h1>

    const nextDay = new Date(currentDate)              <p className="text-xs text-muted-foreground font-medium">ML-Powered Analytics</p>

    nextDay.setDate(nextDay.getDate() + 1)            </div>

    setCurrentDate(nextDay)          </Link>

  }          <nav className="hidden md:flex items-center gap-8">

            <Link href="/schedule" className="text-sm font-semibold text-primary relative">

  const goToToday = () => {              Schedule

    setCurrentDate(new Date())              <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary" />

  }            </Link>

            <Link href="/live" className="text-sm font-semibold hover:text-primary transition-colors">

  const formatDate = (date: Date) => {              Live

    const today = new Date()            </Link>

    const tomorrow = new Date(today)            <Link href="/chemistry" className="text-sm font-semibold hover:text-primary transition-colors">

    tomorrow.setDate(tomorrow.getDate() + 1)              Chemistry

    const yesterday = new Date(today)            </Link>

    yesterday.setDate(yesterday.getDate() - 1)            <Link href="/sentiment" className="text-sm font-semibold hover:text-primary transition-colors">

              Sentiment

    const dateStr = date.toISOString().split('T')[0]            </Link>

    const todayStr = today.toISOString().split('T')[0]            <Link href="/postgame" className="text-sm font-semibold hover:text-primary transition-colors">

    const tomorrowStr = tomorrow.toISOString().split('T')[0]              Analytics

    const yesterdayStr = yesterday.toISOString().split('T')[0]            </Link>

          </nav>

    if (dateStr === todayStr) return "Today"        </div>

    if (dateStr === tomorrowStr) return "Tomorrow"      </header>

    if (dateStr === yesterdayStr) return "Yesterday"

      <main className="container mx-auto px-6 py-12">

    return date.toLocaleDateString('en-US', {        <div className="mb-12">

      weekday: 'long',          <Link

      month: 'long',            href="/"

      day: 'numeric',            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6 group"

      year: 'numeric'          >

    })            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />

  }            <span className="font-medium">Back to Home</span>

          </Link>

  const getStatusBadge = (status: string) => {

    const isLive = status && (          <div className="flex items-center gap-4 mb-6">

      status.toLowerCase().includes('live') ||            <Calendar className="w-12 h-12 text-primary glow" />

      status.toLowerCase().includes('q') ||            <div>

      status.includes(':')              <h1 className="text-6xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

    )                Game Schedule

    const isFinal = status && status.toLowerCase().includes('final')              </h1>

              <p className="text-xl text-muted-foreground font-medium mt-2">ML-powered pregame analysis</p>

    if (isLive) {            </div>

      return (          </div>

        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">        </div>

          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>

          LIVE        <Card className="p-8 mb-12 glass-strong border-2">

        </span>          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">

      )            <div className="flex-1">

    } else if (isFinal) {              <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3 block">

      return (                Select Date

        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500/30">              </label>

          FINAL              <input

        </span>                type="date"

      )                value={selectedDate}

    } else {                onChange={(e) => setSelectedDate(e.target.value)}

      return (                className="w-full md:w-auto px-6 py-4 rounded-xl border-2 border-border bg-background text-foreground font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"

        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">              />

          {status || 'SCHEDULED'}            </div>

        </span>            <div className="flex items-center gap-6 text-sm">

      )              <div className="flex items-center gap-2">

    }                <div className="w-3 h-3 rounded-full bg-primary" />

  }                <span className="font-medium">High Confidence</span>

              </div>

  return (              <div className="flex items-center gap-2">

    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950/20 to-gray-950 p-6">                <div className="w-3 h-3 rounded-full bg-secondary" />

      {/* Header */}                <span className="font-medium">Medium Confidence</span>

      <div className="max-w-7xl mx-auto mb-8">              </div>

        <div className="flex items-center justify-between mb-6">              <div className="flex items-center gap-2">

          <div>                <div className="w-3 h-3 rounded-full bg-muted-foreground" />

            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-600 bg-clip-text text-transparent mb-2 flex items-center gap-3">                <span className="font-medium">Low Confidence</span>

              <Calendar className="w-10 h-10 text-blue-500" />              </div>

              NBA Schedule            </div>

            </h1>          </div>

            <p className="text-gray-400">        </Card>

              Browse games by date and view predictions

            </p>        <div className="space-y-6">

          </div>          {mockGames.map((game) => (

            <Card

          <button              key={game.id}

            onClick={() => fetchGames(currentDate)}              className="p-8 glass-strong border-2 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group"

            disabled={loading}            >

            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"              <div className="flex items-center justify-between mb-6">

          >                <div className="flex items-center gap-3">

            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />                  <div

            Refresh                    className={`w-3 h-3 rounded-full ${

          </button>                      game.confidence === "high"

        </div>                        ? "bg-primary"

                        : game.confidence === "medium"

        {/* Date Navigation */}                          ? "bg-secondary"

        <div className="glass-strong rounded-2xl p-6 mb-6">                          : "bg-muted-foreground"

          <div className="flex items-center justify-between">                    } glow`}

            <button                  />

              onClick={goToPreviousDay}                  <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">{game.time}</span>

              className="p-2 hover:bg-white/10 rounded-lg transition-colors"                </div>

            >                <span

              <ChevronLeft className="w-6 h-6 text-gray-400" />                  className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${

            </button>                    game.confidence === "high"

                      ? "bg-primary/20 text-primary"

            <div className="flex items-center gap-4">                      : game.confidence === "medium"

              <div className="text-center">                        ? "bg-secondary/20 text-secondary"

                <p className="text-2xl font-bold text-white">{formatDate(currentDate)}</p>                        : "bg-muted text-muted-foreground"

                <p className="text-sm text-gray-500 mt-1">                  }`}

                  {currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}                >

                </p>                  {game.confidence} confidence

              </div>                </span>

              </div>

              {currentDate.toISOString().split('T')[0] !== new Date().toISOString().split('T')[0] && (

                <button              <div className="grid md:grid-cols-3 gap-8 items-center">

                  onClick={goToToday}                {/* Away Team */}

                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"                <div className="text-center md:text-right space-y-3">

                >                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>

                  Today                    {game.awayTeam}

                </button>                  </h3>

              )}                  <div className="flex items-center justify-center md:justify-end gap-4 text-sm text-muted-foreground">

            </div>                    <span className="font-semibold">{game.awayRecord}</span>

                    <span>•</span>

            <button                    <span className="font-semibold">Elo: {game.awayElo}</span>

              onClick={goToNextDay}                  </div>

              className="p-2 hover:bg-white/10 rounded-lg transition-colors"                  <div className="flex items-center justify-center md:justify-end gap-2">

            >                    <span className="text-5xl font-black text-primary">{(game.awayWinProb * 100).toFixed(0)}%</span>

              <ChevronRight className="w-6 h-6 text-gray-400" />                    {game.awayWinProb > 0.5 ? (

            </button>                      <TrendingUp className="w-8 h-8 text-primary" />

          </div>                    ) : game.awayWinProb < 0.5 ? (

        </div>                      <TrendingDown className="w-8 h-8 text-muted-foreground" />

                    ) : (

        {/* Stats Summary */}                      <Minus className="w-8 h-8 text-muted-foreground" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">                    )}

          <div className="glass-strong rounded-xl p-4">                  </div>

            <div className="flex items-center gap-3">                </div>

              <div className="p-2 bg-blue-500/20 rounded-lg">

                <Calendar className="w-5 h-5 text-blue-400" />                {/* VS Divider */}

              </div>                <div className="flex flex-col items-center justify-center">

              <div>                  <div

                <p className="text-2xl font-bold text-white">{games.length}</p>                    className="text-4xl font-black text-muted-foreground mb-4"

                <p className="text-sm text-gray-400">Games</p>                    style={{ fontFamily: "var(--font-display)" }}

              </div>                  >

            </div>                    VS

          </div>                  </div>

                  <div className="w-full h-3 bg-muted rounded-full overflow-hidden">

          <div className="glass-strong rounded-xl p-4">                    <div

            <div className="flex items-center gap-3">                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500"

              <div className="p-2 bg-red-500/20 rounded-lg">                      style={{ width: `${game.awayWinProb * 100}%` }}

                <div className="w-5 h-5 flex items-center justify-center">                    />

                  <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>                  </div>

                </div>                  <div className="mt-4 text-sm text-muted-foreground font-semibold">

              </div>                    Predicted Spread: {game.awayWinProb > game.homeWinProb ? "Away" : "Home"} by{" "}

              <div>                    {Math.abs((game.awayWinProb - game.homeWinProb) * 20).toFixed(1)}

                <p className="text-2xl font-bold text-white">                  </div>

                  {games.filter(g => g.status?.toLowerCase().includes('live') || g.status?.toLowerCase().includes('q')).length}                </div>

                </p>

                <p className="text-sm text-gray-400">Live</p>                {/* Home Team */}

              </div>                <div className="text-center md:text-left space-y-3">

            </div>                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>

          </div>                    {game.homeTeam}

                  </h3>

          <div className="glass-strong rounded-xl p-4">                  <div className="flex items-center justify-center md:justify-start gap-4 text-sm text-muted-foreground">

            <div className="flex items-center gap-3">                    <span className="font-semibold">{game.homeRecord}</span>

              <div className="p-2 bg-green-500/20 rounded-lg">                    <span>•</span>

                <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">                    <span className="font-semibold">Elo: {game.homeElo}</span>

                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />                  </div>

                </svg>                  <div className="flex items-center justify-center md:justify-start gap-2">

              </div>                    {game.homeWinProb > 0.5 ? (

              <div>                      <TrendingUp className="w-8 h-8 text-primary" />

                <p className="text-2xl font-bold text-white">                    ) : game.homeWinProb < 0.5 ? (

                  {games.filter(g => g.status?.toLowerCase().includes('final')).length}                      <TrendingDown className="w-8 h-8 text-muted-foreground" />

                </p>                    ) : (

                <p className="text-sm text-gray-400">Completed</p>                      <Minus className="w-8 h-8 text-muted-foreground" />

              </div>                    )}

            </div>                    <span className="text-5xl font-black text-primary">{(game.homeWinProb * 100).toFixed(0)}%</span>

          </div>                  </div>

        </div>                </div>

      </div>              </div>



      {/* Games List */}              {/* Key Factors */}

      <div className="max-w-7xl mx-auto">              <div className="mt-8 pt-8 border-t border-border">

        {loading && games.length === 0 ? (                <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Key Factors</h4>

          <div className="flex flex-col items-center justify-center py-20">                <div className="grid md:grid-cols-3 gap-4 text-sm">

            <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mb-4" />                  <div className="flex items-center gap-2">

            <p className="text-gray-400">Loading games...</p>                    <div className="w-2 h-2 rounded-full bg-primary" />

          </div>                    <span className="text-muted-foreground">

        ) : error ? (                      Home advantage: <span className="font-bold text-foreground">+3.2%</span>

          <div className="glass-strong rounded-2xl p-8 text-center">                    </span>

            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />                  </div>

            <p className="text-red-400 mb-2">Failed to load games</p>                  <div className="flex items-center gap-2">

            <p className="text-gray-500 text-sm">{error}</p>                    <div className="w-2 h-2 rounded-full bg-secondary" />

            <button                    <span className="text-muted-foreground">

              onClick={() => fetchGames(currentDate)}                      Recent form: <span className="font-bold text-foreground">+2.1%</span>

              className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"                    </span>

            >                  </div>

              Try Again                  <div className="flex items-center gap-2">

            </button>                    <div className="w-2 h-2 rounded-full bg-chart-3" />

          </div>                    <span className="text-muted-foreground">

        ) : games.length === 0 ? (                      Rest differential: <span className="font-bold text-foreground">+1.5%</span>

          <div className="glass-strong rounded-2xl p-12 text-center">                    </span>

            <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />                  </div>

            <p className="text-xl text-gray-400 mb-2">No games scheduled</p>                </div>

            <p className="text-gray-500">There are no NBA games on {formatDate(currentDate)}</p>              </div>

            <div className="flex gap-4 justify-center mt-6">            </Card>

              <button          ))}

                onClick={goToPreviousDay}        </div>

                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"      </main>

              >    </div>

                Previous Day  )

              </button>}

              <button
                onClick={goToNextDay}
                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Next Day
              </button>
            </div>
          </div>
        ) : (
          <div className="grid gap-4">
            {games.map((game, index) => (
              <div
                key={game.game_id || index}
                className="glass-strong rounded-2xl p-6 hover:bg-white/5 transition-all duration-200 group"
              >
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    {getStatusBadge(game.status)}
                    <span className="text-sm text-gray-500">
                      {new Date(game.date).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>

                  <Link
                    href={`/predictions/${game.game_id}`}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    View Prediction
                  </Link>
                </div>

                {/* Teams */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Away Team */}
                  <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold">
                        {game.visitor_team?.abbreviation || 'TBD'}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {game.visitor_team?.name || 'TBD'}
                        </p>
                        <p className="text-sm text-gray-500">Away</p>
                      </div>
                    </div>
                    {game.visitor_team?.score !== undefined && (
                      <div className="text-3xl font-bold text-white">
                        {game.visitor_team.score}
                      </div>
                    )}
                  </div>

                  {/* Home Team */}
                  <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center text-white font-bold">
                        {game.home_team?.abbreviation || 'TBD'}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {game.home_team?.name || 'TBD'}
                        </p>
                        <p className="text-sm text-gray-500">Home</p>
                      </div>
                    </div>
                    {game.home_team?.score !== undefined && (
                      <div className="text-3xl font-bold text-white">
                        {game.home_team.score}
                      </div>
                    )}
                  </div>
                </div>

                {/* Prediction Placeholder */}
                {(!game.status || game.status.toLowerCase().includes('scheduled')) && (
                  <div className="mt-6 pt-4 border-t border-gray-800">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Win Probability:</span>
                      <span className="text-blue-400">Coming soon...</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
