"use client""use client""use client"



import { useState, useEffect } from "react"

import Link from "next/link"

import { ArrowLeft, Calendar, ChevronLeft, ChevronRight, RefreshCw, Clock, MapPin } from "lucide-react"import { useEffect, useState } from "react"import { useState } from "react"



interface Game {import { Calendar, ChevronLeft, ChevronRight, RefreshCw, AlertCircle } from "lucide-react"import Link from "next/link"

  game_id: string

  date: stringimport Link from "next/link"import { ArrowLeft, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react"

  home_team: string

  away_team: stringimport { Card } from "@/components/ui/card"

  game_time: string

  season: stringinterface Team {

}

  id: numberconst mockGames = [

interface GamesByDate {

  [date: string]: Game[]  name: string  {

}

  abbreviation: string    id: "1",

export default function SchedulePage() {

  const [gamesByDate, setGamesByDate] = useState<GamesByDate>({})  score: number    date: "2025-10-27",

  const [dates, setDates] = useState<string[]>([])

  const [loading, setLoading] = useState(true)}    time: "7:30 PM ET",

  const [currentMonth, setCurrentMonth] = useState<string>(new Date().toISOString().slice(0, 7))

    homeTeam: "Los Angeles Lakers",

  const fetchSchedule = async (month: string) => {

    setLoading(true)interface Game {    awayTeam: "Boston Celtics",

    try {

      const response = await fetch(`/api/schedule?month=${month}`)  game_id: string    homeWinProb: 0.4,

      const data = await response.json()

        date: string    awayWinProb: 0.6,

      if (data.success) {

        setGamesByDate(data.gamesByDate || {})  status: string    homeElo: 1620,

        setDates(data.dates || [])

      }  home_team: Team    awayElo: 1650,

    } catch (error) {

      console.error('Failed to fetch schedule:', error)  visitor_team: Team    homeRecord: "25-15",

    } finally {

      setLoading(false)}    awayRecord: "28-12",

    }

  }    confidence: "medium",



  useEffect(() => {interface GamesResponse {  },

    fetchSchedule(currentMonth)

  }, [currentMonth])  success: boolean  {



  const changeMonth = (direction: 'prev' | 'next') => {  count: number    id: "2",

    const [year, month] = currentMonth.split('-').map(Number)

    let newYear = year  games: Game[]    date: "2025-10-27",

    let newMonth = month

}    time: "8:00 PM ET",

    if (direction === 'prev') {

      newMonth--    homeTeam: "Golden State Warriors",

      if (newMonth < 1) {

        newMonth = 12export default function SchedulePage() {    awayTeam: "Milwaukee Bucks",

        newYear--

      }  const [games, setGames] = useState<Game[]>([])    homeWinProb: 0.55,

    } else {

      newMonth++  const [loading, setLoading] = useState(true)    awayWinProb: 0.45,

      if (newMonth > 12) {

        newMonth = 1  const [error, setError] = useState<string | null>(null)    homeElo: 1640,

        newYear++

      }  const [currentDate, setCurrentDate] = useState<Date>(new Date())    awayElo: 1625,

    }

    homeRecord: "27-13",

    setCurrentMonth(`${newYear}-${String(newMonth).padStart(2, '0')}`)

  }  const fetchGames = async (date: Date) => {    awayRecord: "26-14",



  const formatDate = (dateStr: string) => {    setLoading(true)    confidence: "high",

    const date = new Date(dateStr + 'T00:00:00')

    return date.toLocaleDateString('en-US', {     setError(null)  },

      weekday: 'short',

      month: 'short',   {

      day: 'numeric',

      year: 'numeric'    try {    id: "3",

    })

  }      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"    date: "2025-10-27",



  const formatMonthYear = (monthStr: string) => {      const dateStr = date.toISOString().split('T')[0]    time: "9:30 PM ET",

    const [year, month] = monthStr.split('-')

    const date = new Date(parseInt(year), parseInt(month) - 1)      const response = await fetch(`${backendUrl}/api/games?date=${dateStr}`)    homeTeam: "Phoenix Suns",

    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  }    awayTeam: "Denver Nuggets",



  const isToday = (dateStr: string) => {      if (!response.ok) {    homeWinProb: 0.48,

    const today = new Date().toISOString().split('T')[0]

    return dateStr === today        throw new Error(`HTTP error! status: ${response.status}`)    awayWinProb: 0.52,

  }

      }    homeElo: 1630,

  return (

    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">    awayElo: 1635,

      {/* Navigation Bar */}

      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-slate-700/50">      const data: GamesResponse = await response.json()    homeRecord: "26-14",

        <div className="container mx-auto px-6 py-4">

          <div className="flex items-center justify-between">      setGames(data.games || [])    awayRecord: "27-13",

            <div className="flex items-center gap-8">

              <Link href="/" className="flex items-center gap-3 group">    } catch (err) {    confidence: "low",

                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">

                  🏀      setError(err instanceof Error ? err.message : "Failed to fetch games")  },

                </div>

                <span className="text-xl font-bold text-white">NBA Intel</span>      console.error("Error:", err)]

              </Link>

              <div className="hidden md:flex items-center gap-6">    } finally {

                <Link href="/" className="text-slate-300 hover:text-white transition-colors flex items-center gap-2">

                  <ArrowLeft className="w-4 h-4" />      setLoading(false)export default function SchedulePage() {

                  Back to Home

                </Link>    }  const [selectedDate, setSelectedDate] = useState("2025-10-27")

                <Link href="/predictions" className="text-slate-300 hover:text-blue-400 transition-colors">

                  Predictions  }

                </Link>

                <Link href="/live" className="text-slate-300 hover:text-blue-400 transition-colors">  return (

                  Live

                </Link>  useEffect(() => {    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">

              </div>

            </div>    fetchGames(currentDate)      <header className="glass-strong sticky top-0 z-50 border-b">

            <button

              onClick={() => fetchSchedule(currentMonth)}  }, [currentDate])        <div className="container mx-auto px-6 py-6 flex items-center justify-between">

              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"

            >          <Link href="/" className="flex items-center gap-3 group">

              <RefreshCw className="w-5 h-5" />

            </button>  const goToPreviousDay = () => {            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow-lg group-hover:scale-110 transition-transform duration-300">

          </div>

        </div>    const prevDay = new Date(currentDate)              🏀

      </nav>

    prevDay.setDate(prevDay.getDate() - 1)            </div>

      {/* Header */}

      <div className="container mx-auto px-6 py-12">    setCurrentDate(prevDay)            <div>

        <div className="text-center mb-12">

          <div className="flex items-center justify-center gap-4 mb-6">  }              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/50">

              <Calendar className="w-10 h-10 text-white" />                NBA Intel

            </div>

          </div>  const goToNextDay = () => {              </h1>

          <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">

            NBA Schedule    const nextDay = new Date(currentDate)              <p className="text-xs text-muted-foreground font-medium">ML-Powered Analytics</p>

          </h1>

          <p className="text-xl text-slate-300">    nextDay.setDate(nextDay.getDate() + 1)            </div>

            Complete 2024-25 Season Schedule

          </p>    setCurrentDate(nextDay)          </Link>

        </div>

  }          <nav className="hidden md:flex items-center gap-8">

        {/* Month Navigator */}

        <div className="flex items-center justify-center gap-6 mb-12">            <Link href="/schedule" className="text-sm font-semibold text-primary relative">

          <button

            onClick={() => changeMonth('prev')}  const goToToday = () => {              Schedule

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"

          >    setCurrentDate(new Date())              <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary" />

            <ChevronLeft className="w-6 h-6" />

          </button>  }            </Link>

          <div className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-2xl shadow-lg">

            {formatMonthYear(currentMonth)}            <Link href="/live" className="text-sm font-semibold hover:text-primary transition-colors">

          </div>

          <button  const formatDate = (date: Date) => {              Live

            onClick={() => changeMonth('next')}

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"    const today = new Date()            </Link>

          >

            <ChevronRight className="w-6 h-6" />    const tomorrow = new Date(today)            <Link href="/chemistry" className="text-sm font-semibold hover:text-primary transition-colors">

          </button>

        </div>    tomorrow.setDate(tomorrow.getDate() + 1)              Chemistry



        {/* Loading State */}    const yesterday = new Date(today)            </Link>

        {loading && (

          <div className="text-center py-20">    yesterday.setDate(yesterday.getDate() - 1)            <Link href="/sentiment" className="text-sm font-semibold hover:text-primary transition-colors">

            <div className="inline-block w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>

            <p className="mt-4 text-slate-400">Loading schedule...</p>              Sentiment

          </div>

        )}    const dateStr = date.toISOString().split('T')[0]            </Link>



        {/* Games by Date */}    const todayStr = today.toISOString().split('T')[0]            <Link href="/postgame" className="text-sm font-semibold hover:text-primary transition-colors">

        {!loading && dates.length === 0 && (

          <div className="text-center py-20">    const tomorrowStr = tomorrow.toISOString().split('T')[0]              Analytics

            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />

            <p className="text-xl text-slate-400">No games scheduled for this month</p>    const yesterdayStr = yesterday.toISOString().split('T')[0]            </Link>

          </div>

        )}          </nav>



        {!loading && dates.length > 0 && (    if (dateStr === todayStr) return "Today"        </div>

          <div className="space-y-8">

            {dates.map((date) => (    if (dateStr === tomorrowStr) return "Tomorrow"      </header>

              <div key={date} className="space-y-4">

                {/* Date Header */}    if (dateStr === yesterdayStr) return "Yesterday"

                <div className={`flex items-center gap-4 px-6 py-4 rounded-xl ${

                  isToday(date)      <main className="container mx-auto px-6 py-12">

                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 shadow-lg shadow-green-500/30'

                    : 'bg-slate-800/80'    return date.toLocaleDateString('en-US', {        <div className="mb-12">

                }`}>

                  <Calendar className="w-6 h-6 text-white" />      weekday: 'long',          <Link

                  <h2 className="text-2xl font-bold text-white">

                    {formatDate(date)}      month: 'long',            href="/"

                    {isToday(date) && (

                      <span className="ml-3 text-sm font-semibold bg-white/20 px-3 py-1 rounded-full">      day: 'numeric',            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6 group"

                        TODAY

                      </span>      year: 'numeric'          >

                    )}

                  </h2>    })            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />

                  <span className="ml-auto text-slate-300 font-semibold">

                    {gamesByDate[date]?.length || 0} games  }            <span className="font-medium">Back to Home</span>

                  </span>

                </div>          </Link>



                {/* Games Grid */}  const getStatusBadge = (status: string) => {

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                  {gamesByDate[date]?.map((game) => (    const isLive = status && (          <div className="flex items-center gap-4 mb-6">

                    <div

                      key={game.game_id}      status.toLowerCase().includes('live') ||            <Calendar className="w-12 h-12 text-primary glow" />

                      className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/20"

                    >      status.toLowerCase().includes('q') ||            <div>

                      {/* Game Time */}

                      <div className="flex items-center gap-2 mb-4 text-slate-400">      status.includes(':')              <h1 className="text-6xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

                        <Clock className="w-4 h-4" />

                        <span className="text-sm font-medium">{game.game_time}</span>    )                Game Schedule

                      </div>

    const isFinal = status && status.toLowerCase().includes('final')              </h1>

                      {/* Teams */}

                      <div className="space-y-3">              <p className="text-xl text-muted-foreground font-medium mt-2">ML-powered pregame analysis</p>

                        {/* Away Team */}

                        <div className="flex items-center justify-between">    if (isLive) {            </div>

                          <div className="flex items-center gap-3">

                            <MapPin className="w-4 h-4 text-slate-500" />      return (          </div>

                            <span className="text-slate-400 text-sm">@</span>

                            <span className="text-2xl font-bold text-white">        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">        </div>

                              {game.away_team}

                            </span>          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>

                          </div>

                        </div>          LIVE        <Card className="p-8 mb-12 glass-strong border-2">



                        {/* VS Divider */}        </span>          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">

                        <div className="flex items-center gap-2">

                          <div className="h-px bg-slate-700 flex-1"></div>      )            <div className="flex-1">

                          <span className="text-slate-500 text-xs font-semibold">VS</span>

                          <div className="h-px bg-slate-700 flex-1"></div>    } else if (isFinal) {              <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3 block">

                        </div>

      return (                Select Date

                        {/* Home Team */}

                        <div className="flex items-center justify-between">        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500/30">              </label>

                          <div className="flex items-center gap-3">

                            <div className="w-4 h-4 rounded-full bg-blue-500"></div>          FINAL              <input

                            <span className="text-2xl font-bold text-white">

                              {game.home_team}        </span>                type="date"

                            </span>

                          </div>      )                value={selectedDate}

                        </div>

                      </div>    } else {                onChange={(e) => setSelectedDate(e.target.value)}



                      {/* View Prediction Button */}      return (                className="w-full md:w-auto px-6 py-4 rounded-xl border-2 border-border bg-background text-foreground font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"

                      <Link

                        href={`/predictions?date=${date}`}        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">              />

                        className="mt-4 w-full py-2 px-4 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-sm font-semibold text-center block transition-all"

                      >          {status || 'SCHEDULED'}            </div>

                        View Prediction

                      </Link>        </span>            <div className="flex items-center gap-6 text-sm">

                    </div>

                  ))}      )              <div className="flex items-center gap-2">

                </div>

              </div>    }                <div className="w-3 h-3 rounded-full bg-primary" />

            ))}

          </div>  }                <span className="font-medium">High Confidence</span>

        )}

      </div>              </div>



      {/* Quick Stats Footer */}  return (              <div className="flex items-center gap-2">

      <div className="container mx-auto px-6 py-12 mt-12">

        <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950/20 to-gray-950 p-6">                <div className="w-3 h-3 rounded-full bg-secondary" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">

            <div>      {/* Header */}                <span className="font-medium">Medium Confidence</span>

              <div className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">

                {dates.length}      <div className="max-w-7xl mx-auto mb-8">              </div>

              </div>

              <div className="text-slate-400">Game Days This Month</div>        <div className="flex items-center justify-between mb-6">              <div className="flex items-center gap-2">

            </div>

            <div>          <div>                <div className="w-3 h-3 rounded-full bg-muted-foreground" />

              <div className="text-4xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">

                {Object.values(gamesByDate).flat().length}            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-600 bg-clip-text text-transparent mb-2 flex items-center gap-3">                <span className="font-medium">Low Confidence</span>

              </div>

              <div className="text-slate-400">Total Games</div>              <Calendar className="w-10 h-10 text-blue-500" />              </div>

            </div>

            <div>              NBA Schedule            </div>

              <div className="text-4xl font-black bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent mb-2">

                2024-25            </h1>          </div>

              </div>

              <div className="text-slate-400">NBA Season</div>            <p className="text-gray-400">        </Card>

            </div>

          </div>              Browse games by date and view predictions

        </div>

      </div>            </p>        <div className="space-y-6">

    </div>

  )          </div>          {mockGames.map((game) => (

}

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
