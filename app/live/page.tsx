"use client""use client"



import { useEffect, useState } from "react"import { NavHeader } from "@/components/nav-header"

import { RefreshCw, Activity, Clock, TrendingUp, AlertCircle } from "lucide-react"import { Card } from "@/components/ui/card"

import Link from "next/link"import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"



interface Team {// Mock data for demonstration

  id: numberconst mockData = [

  name: string  { possession: 0, homeWinProb: 0.52 },

  abbreviation: string  { possession: 10, homeWinProb: 0.55 },

  score: number  { possession: 20, homeWinProb: 0.58 },

}  { possession: 30, homeWinProb: 0.62 },

  { possession: 40, homeWinProb: 0.59 },

interface Game {  { possession: 50, homeWinProb: 0.65 },

  game_id: string  { possession: 60, homeWinProb: 0.68 },

  date: string]

  status: string

  home_team: Teamexport default function LivePage() {

  visitor_team: Team  return (

  period?: number    <div className="min-h-screen bg-background">

  time_remaining?: string      <NavHeader />

}

      <main className="container mx-auto px-4 py-8">

interface LiveGamesResponse {        <div className="mb-8">

  success: boolean          <h1 className="text-4xl font-bold mb-2">📊 Live Game Center</h1>

  count: number          <p className="text-muted-foreground text-lg">Real-time win probability powered by GRU sequences</p>

  games: Game[]        </div>

}

        <div className="grid lg:grid-cols-3 gap-6">

export default function LivePage() {          <div className="lg:col-span-2 space-y-6">

  const [liveGames, setLiveGames] = useState<Game[]>([])            <Card className="p-6">

  const [loading, setLoading] = useState(true)              <div className="flex items-center justify-between mb-6">

  const [error, setError] = useState<string | null>(null)                <div>

  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())                  <h2 className="text-2xl font-bold">Lakers vs Warriors</h2>

                  <div className="flex items-center gap-2 mt-1">

  const fetchLiveGames = async () => {                    <p className="text-muted-foreground">Q3 • 5:23 remaining</p>

    try {                    <span className="px-2 py-1 text-xs font-medium bg-destructive/20 text-destructive rounded-full animate-pulse">

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"                      LIVE

      const response = await fetch(`${backendUrl}/api/games/live`)                    </span>

                  </div>

      if (!response.ok) {                </div>

        throw new Error(`HTTP error! status: ${response.status}`)                <div className="text-right">

      }                  <div className="text-4xl font-bold">98 - 94</div>

                </div>

      const data: LiveGamesResponse = await response.json()              </div>

      setLiveGames(data.games || [])

      setLastUpdate(new Date())              <div className="mb-2 flex justify-between text-sm">

      setError(null)                <span>Lakers Win Probability</span>

    } catch (err) {                <span className="font-bold text-primary text-lg">68%</span>

      setError(err instanceof Error ? err.message : "Failed to fetch live games")              </div>

      console.error("Error:", err)              <div className="h-3 bg-muted rounded-full overflow-hidden">

    } finally {                <div className="h-full bg-primary transition-all duration-500" style={{ width: "68%" }} />

      setLoading(false)              </div>

    }            </Card>

  }

            <Card className="p-6">

  useEffect(() => {              <h3 className="text-xl font-semibold mb-4">Win Probability Chart</h3>

    fetchLiveGames()              <ResponsiveContainer width="100%" height={350}>

    // Auto-refresh every 30 seconds for live data                <LineChart data={mockData}>

    const interval = setInterval(() => fetchLiveGames(), 30 * 1000)                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />

    return () => clearInterval(interval)                  <XAxis

  }, [])                    dataKey="possession"

                    className="text-muted-foreground"

  const getQuarter = (period: number | undefined) => {                    label={{ value: "Possession", position: "insideBottom", offset: -5 }}

    if (!period) return 'N/A'                  />

    if (period <= 4) return `Q${period}`                  <YAxis

    return `OT${period - 4}`                    className="text-muted-foreground"

  }                    domain={[0, 1]}

                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}

  const calculateScoreDiff = (game: Game) => {                  />

    const homeScore = game.home_team?.score || 0                  <Tooltip

    const awayScore = game.visitor_team?.score || 0                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}

    return Math.abs(homeScore - awayScore)                    formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, "Win Probability"]}

  }                  />

                  <Line

  const getLeadingTeam = (game: Game) => {                    type="monotone"

    const homeScore = game.home_team?.score || 0                    dataKey="homeWinProb"

    const awayScore = game.visitor_team?.score || 0                    stroke="hsl(var(--primary))"

                        strokeWidth={3}

    if (homeScore > awayScore) return 'home'                    dot={false}

    if (awayScore > homeScore) return 'away'                  />

    return 'tie'                </LineChart>

  }              </ResponsiveContainer>

            </Card>

  return (          </div>

    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-red-950/20 to-gray-950 p-6">

      {/* Header */}          <div className="space-y-6">

      <div className="max-w-7xl mx-auto mb-8">            <Card className="p-6">

        <div className="flex items-center justify-between mb-6">              <h3 className="text-lg font-semibold mb-4">Play-by-Play</h3>

          <div>              <div className="space-y-3 text-sm max-h-96 overflow-y-auto">

            <h1 className="text-4xl font-bold bg-gradient-to-r from-red-400 to-orange-600 bg-clip-text text-transparent mb-2 flex items-center gap-3">                <div className="pb-3 border-b border-border">

              <Activity className="w-10 h-10 text-red-500" />                  <p className="font-medium">5:23 Q3</p>

              Live Game Center                  <p className="text-muted-foreground">LeBron James makes 3-pt shot</p>

            </h1>                  <p className="text-xs text-primary mt-1">Win prob: 68% (+3%)</p>

            <p className="text-gray-400">                </div>

              Real-time scores and updates • Refreshing every 30 seconds                <div className="pb-3 border-b border-border">

            </p>                  <p className="font-medium">5:45 Q3</p>

          </div>                  <p className="text-muted-foreground">Stephen Curry misses jumper</p>

                            <p className="text-xs text-muted-foreground mt-1">Win prob: 65%</p>

          <button                </div>

            onClick={() => fetchLiveGames()}                <div className="pb-3 border-b border-border">

            disabled={loading}                  <p className="font-medium">6:12 Q3</p>

            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"                  <p className="text-muted-foreground">Anthony Davis defensive rebound</p>

          >                  <p className="text-xs text-muted-foreground mt-1">Win prob: 65%</p>

            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />                </div>

            Refresh                <div className="pb-3 border-b border-border">

          </button>                  <p className="font-medium">6:34 Q3</p>

        </div>                  <p className="text-muted-foreground">Klay Thompson makes 2-pt shot</p>

                  <p className="text-xs text-destructive mt-1">Win prob: 62% (-3%)</p>

        {/* Stats Cards */}                </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">              </div>

          <div className="glass-strong rounded-xl p-4">            </Card>

            <div className="flex items-center gap-3">

              <div className="p-2 bg-red-500/20 rounded-lg">            <Card className="p-6">

                <Activity className="w-5 h-5 text-red-400" />              <h3 className="text-lg font-semibold mb-4">Key Factors (SHAP)</h3>

              </div>              <div className="space-y-3 text-sm">

              <div>                <div className="flex justify-between items-center">

                <p className="text-2xl font-bold text-white">{liveGames.length}</p>                  <span className="text-muted-foreground">Recent momentum</span>

                <p className="text-sm text-gray-400">Live Games</p>                  <span className="font-medium text-primary">+12%</span>

              </div>                </div>

            </div>                <div className="flex justify-between items-center">

          </div>                  <span className="text-muted-foreground">Foul trouble</span>

                  <span className="font-medium text-destructive">-3%</span>

          <div className="glass-strong rounded-xl p-4">                </div>

            <div className="flex items-center gap-3">                <div className="flex justify-between items-center">

              <div className="p-2 bg-orange-500/20 rounded-lg">                  <span className="text-muted-foreground">Lineup strength</span>

                <TrendingUp className="w-5 h-5 text-orange-400" />                  <span className="font-medium text-primary">+8%</span>

              </div>                </div>

              <div>                <div className="flex justify-between items-center">

                <p className="text-2xl font-bold text-white">                  <span className="text-muted-foreground">Time remaining</span>

                  {liveGames.filter(g => calculateScoreDiff(g) <= 5).length}                  <span className="font-medium">+5%</span>

                </p>                </div>

                <p className="text-sm text-gray-400">Close Games</p>              </div>

              </div>            </Card>

            </div>          </div>

          </div>        </div>

      </main>

          <div className="glass-strong rounded-xl p-4">    </div>

            <div className="flex items-center gap-3">  )

              <div className="p-2 bg-yellow-500/20 rounded-lg">}

                <Clock className="w-5 h-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm font-mono text-white">
                  {lastUpdate.toLocaleTimeString()}
                </p>
                <p className="text-sm text-gray-400">Last Update</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Games List */}
      <div className="max-w-7xl mx-auto">
        {loading && liveGames.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <RefreshCw className="w-12 h-12 text-red-500 animate-spin mb-4" />
            <p className="text-gray-400">Loading live games...</p>
          </div>
        ) : error ? (
          <div className="glass-strong rounded-2xl p-8 text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-400 mb-2">Failed to load live games</p>
            <p className="text-gray-500 text-sm">{error}</p>
            <button
              onClick={() => fetchLiveGames()}
              className="mt-4 px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
            >
              Try Again
            </button>
          </div>
        ) : liveGames.length === 0 ? (
          <div className="glass-strong rounded-2xl p-12 text-center">
            <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-xl text-gray-400 mb-2">No live games right now</p>
            <p className="text-gray-500 mb-6">Check back when games are in progress</p>
            <Link
              href="/predictions"
              className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              View All Games
            </Link>
          </div>
        ) : (
          <div className="grid gap-6">
            {liveGames.map((game) => {
              const leadingTeam = getLeadingTeam(game)
              const scoreDiff = calculateScoreDiff(game)
              const isCloseGame = scoreDiff <= 5

              return (
                <div
                  key={game.game_id}
                  className="glass-strong rounded-2xl p-6 hover:bg-white/5 transition-all duration-200 group relative overflow-hidden"
                >
                  {/* Live indicator pulse effect */}
                  <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
                  
                  <div className="relative">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
                          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                          LIVE • {getQuarter(game.period)}
                        </span>
                        {game.time_remaining && (
                          <span className="text-sm text-gray-400 font-mono">
                            {game.time_remaining}
                          </span>
                        )}
                        {isCloseGame && (
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-500/20 text-orange-400 border border-orange-500/30">
                            🔥 CLOSE
                          </span>
                        )}
                      </div>
                      
                      <Link
                        href={`/live/${game.game_id}`}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        Watch Live
                      </Link>
                    </div>

                    {/* Teams */}
                    <div className="grid gap-4">
                      {/* Away Team */}
                      <div className={`flex items-center justify-between p-4 rounded-xl transition-all ${
                        leadingTeam === 'away' ? 'bg-green-500/10 border border-green-500/30' : 'bg-gray-800/30'
                      }`}>
                        <div className="flex items-center gap-4">
                          <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                            {game.visitor_team?.abbreviation || 'TBD'}
                          </div>
                          <div>
                            <p className="font-semibold text-white text-lg">
                              {game.visitor_team?.name || 'TBD'}
                            </p>
                            <p className="text-sm text-gray-500">Away</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {leadingTeam === 'away' && (
                            <span className="text-sm text-green-400 font-medium">
                              +{scoreDiff}
                            </span>
                          )}
                          <div className="text-4xl font-bold text-white">
                            {game.visitor_team?.score || 0}
                          </div>
                        </div>
                      </div>

                      {/* Home Team */}
                      <div className={`flex items-center justify-between p-4 rounded-xl transition-all ${
                        leadingTeam === 'home' ? 'bg-green-500/10 border border-green-500/30' : 'bg-gray-800/30'
                      }`}>
                        <div className="flex items-center gap-4">
                          <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                            {game.home_team?.abbreviation || 'TBD'}
                          </div>
                          <div>
                            <p className="font-semibold text-white text-lg">
                              {game.home_team?.name || 'TBD'}
                            </p>
                            <p className="text-sm text-gray-500">Home</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {leadingTeam === 'home' && (
                            <span className="text-sm text-green-400 font-medium">
                              +{scoreDiff}
                            </span>
                          )}
                          <div className="text-4xl font-bold text-white">
                            {game.home_team?.score || 0}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* ML Win Probability (placeholder) */}
                    <div className="mt-6 pt-4 border-t border-gray-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Live Win Probability</span>
                        <span className="text-sm text-gray-500">Powered by GRU Model</span>
                      </div>
                      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: "65%" }}
                        />
                      </div>
                      <div className="flex justify-between mt-1 text-xs text-gray-500">
                        <span>{game.visitor_team?.abbreviation} 35%</span>
                        <span>{game.home_team?.abbreviation} 65%</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
