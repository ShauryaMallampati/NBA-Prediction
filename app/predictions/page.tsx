"use client"

import { useEffect, useState } from "react"
import { RefreshCw, Calendar, TrendingUp, Users, AlertCircle } from "lucide-react"
import Link from "next/link"

interface Team {
  id: number
  name: string
  abbreviation: string
  score: number
}

interface Game {
  game_id: string
  date: string
  status: string
  home_team: Team
  visitor_team: Team
  season?: string
}

interface GamesResponse {
  success: boolean
  count: number
  games: Game[]
}

export default function PredictionsPage() {
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )

  const fetchGames = async (date?: string) => {
    setLoading(true)
    setError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const dateParam = date || selectedDate
      const url = `${backendUrl}/api/games${dateParam ? `?date=${dateParam}` : ''}`
      
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: GamesResponse = await response.json()
      setGames(data.games || [])
      setLastUpdate(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch games")
      console.error("Error:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGames()
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => fetchGames(), 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [selectedDate])

  const getQuickDateOptions = () => {
    const today = new Date()
    const options = []
    
    // Yesterday
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    options.push({ label: 'Yesterday', date: yesterday.toISOString().split('T')[0] })
    
    // Today
    options.push({ label: 'Today', date: today.toISOString().split('T')[0] })
    
    // Tomorrow
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    options.push({ label: 'Tomorrow', date: tomorrow.toISOString().split('T')[0] })
    
    return options
  }

  const getStatusBadge = (status: string) => {
    const isLive = status && (
      status.toLowerCase().includes('live') || 
      status.toLowerCase().includes('q') || 
      status.includes(':')
    )
    const isFinal = status && status.toLowerCase().includes('final')
    
    if (isLive) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
          LIVE
        </span>
      )
    } else if (isFinal) {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500/30">
          FINAL
        </span>
      )
    } else {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
          {status || 'SCHEDULED'}
        </span>
      )
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent mb-2">
              🏀 Game Predictions
            </h1>
            <p className="text-gray-400">
              Real-time NBA games and ML-powered predictions
            </p>
          </div>
          
          <button
            onClick={() => fetchGames()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Date Filter */}
        <div className="glass-strong rounded-2xl p-6 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Calendar className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-gray-400">Select Date:</span>
            
            {/* Quick date buttons */}
            <div className="flex gap-2">
              {getQuickDateOptions().map(option => (
                <button
                  key={option.date}
                  onClick={() => setSelectedDate(option.date)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedDate === option.date
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {/* Date picker */}
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
            />
          </div>
          
          <div className="mt-4 text-xs text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refresh every 5 minutes
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="glass-strong rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Users className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{games.length}</p>
                <p className="text-sm text-gray-400">Total Games</p>
              </div>
            </div>
          </div>

          <div className="glass-strong rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <div className="w-5 h-5 flex items-center justify-center">
                  <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {games.filter(g => g.status?.toLowerCase().includes('live') || g.status?.toLowerCase().includes('q')).length}
                </p>
                <p className="text-sm text-gray-400">Live Games</p>
              </div>
            </div>
          </div>

          <div className="glass-strong rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {games.filter(g => g.status?.toLowerCase().includes('final')).length}
                </p>
                <p className="text-sm text-gray-400">Completed</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Games List */}
      <div className="max-w-7xl mx-auto">
        {loading && games.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mb-4" />
            <p className="text-gray-400">Loading games...</p>
          </div>
        ) : error ? (
          <div className="glass-strong rounded-2xl p-8 text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-400 mb-2">Failed to load games</p>
            <p className="text-gray-500 text-sm">{error}</p>
            <button
              onClick={() => fetchGames()}
              className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
            >
              Try Again
            </button>
          </div>
        ) : games.length === 0 ? (
          <div className="glass-strong rounded-2xl p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-xl text-gray-400 mb-2">No games scheduled</p>
            <p className="text-gray-500">There are no NBA games on {selectedDate}</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {games.map((game) => (
              <div
                key={game.game_id}
                className="glass-strong rounded-2xl p-6 hover:bg-white/5 transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {getStatusBadge(game.status)}
                    <span className="text-sm text-gray-500">
                      {new Date(game.date).toLocaleDateString('en-US', { 
                        weekday: 'short', 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </span>
                  </div>
                  
                  <Link
                    href={`/predictions/${game.game_id}`}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    View Details
                  </Link>
                </div>

                {/* Teams */}
                <div className="grid grid-cols-2 gap-8">
                  {/* Away Team */}
                  <div className="flex items-center justify-between">
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
                    <div className="text-3xl font-bold text-white">
                      {game.visitor_team?.score || '-'}
                    </div>
                  </div>

                  {/* Home Team */}
                  <div className="flex items-center justify-between">
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
                    <div className="text-3xl font-bold text-white">
                      {game.home_team?.score || '-'}
                    </div>
                  </div>
                </div>

                {/* ML Prediction Placeholder */}
                {game.status?.toLowerCase().includes('scheduled') || !game.status && (
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">ML Prediction:</span>
                      <span className="text-purple-400">Coming soon...</span>
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
