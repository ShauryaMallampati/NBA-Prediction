"use client"

import { Activity, Clock, RefreshCw } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

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
  period?: number
  time_remaining?: string
}

interface LiveScoreboardProps {
  autoRefresh?: boolean
  refreshInterval?: number // in seconds
  maxGames?: number
  className?: string
}

export function LiveScoreboard({
  autoRefresh = true,
  refreshInterval = 30,
  maxGames,
  className = "",
}: LiveScoreboardProps) {
  const [liveGames, setLiveGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchLiveGames = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${backendUrl}/api/games/live`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      let games = data.games || []
      
      if (maxGames && games.length > maxGames) {
        games = games.slice(0, maxGames)
      }
      
      setLiveGames(games)
      setLastUpdate(new Date())
    } catch (err) {
      console.error("Error fetching live games:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLiveGames()

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchLiveGames()
      }, refreshInterval * 1000)

      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  const getQuarter = (period: number | undefined) => {
    if (!period) return 'N/A'
    if (period <= 4) return `Q${period}`
    return `OT${period - 4}`
  }

  const getLeadingTeam = (game: Game) => {
    const homeScore = game.home_team?.score || 0
    const awayScore = game.visitor_team?.score || 0
    
    if (homeScore > awayScore) return 'home'
    if (awayScore > homeScore) return 'away'
    return 'tie'
  }

  if (loading && liveGames.length === 0) {
    return (
      <div className={`glass-strong rounded-xl p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-8 h-8 text-purple-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (liveGames.length === 0) {
    return (
      <div className={`glass-strong rounded-xl p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-white">Live Games</h3>
        </div>
        <p className="text-gray-400 text-center py-8">No live games right now</p>
        <Link
          href="/predictions"
          className="block text-center text-sm text-purple-400 hover:text-purple-300 transition-colors"
        >
          View All Games →
        </Link>
      </div>
    )
  }

  return (
    <div className={`glass-strong rounded-xl p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-red-500" />
          <h3 className="text-lg font-semibold text-white">Live Games</h3>
          <span className="px-2 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
            {liveGames.length}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            {lastUpdate.toLocaleTimeString()}
          </div>
          <button
            onClick={() => fetchLiveGames()}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Games List */}
      <div className="space-y-4">
        {liveGames.map((game) => {
          const leadingTeam = getLeadingTeam(game)

          return (
            <Link
              key={game.game_id}
              href={`/live/${game.game_id}`}
              className="block p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all group"
            >
              {/* Status Bar */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                  <span className="text-xs font-semibold text-red-400">
                    LIVE • {getQuarter(game.period)}
                  </span>
                </div>
                {game.time_remaining && (
                  <span className="text-xs text-gray-400 font-mono">
                    {game.time_remaining}
                  </span>
                )}
              </div>

              {/* Teams */}
              <div className="space-y-2">
                {/* Away Team */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center text-white font-bold text-xs">
                      {game.visitor_team?.abbreviation}
                    </div>
                    <span className="text-sm text-white">
                      {game.visitor_team?.name}
                    </span>
                  </div>
                  <div className={`text-lg font-bold ${
                    leadingTeam === 'away' ? 'text-green-400' : 'text-white'
                  }`}>
                    {game.visitor_team?.score || 0}
                  </div>
                </div>

                {/* Home Team */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded flex items-center justify-center text-white font-bold text-xs">
                      {game.home_team?.abbreviation}
                    </div>
                    <span className="text-sm text-white">
                      {game.home_team?.name}
                    </span>
                  </div>
                  <div className={`text-lg font-bold ${
                    leadingTeam === 'home' ? 'text-green-400' : 'text-white'
                  }`}>
                    {game.home_team?.score || 0}
                  </div>
                </div>
              </div>

              {/* View Details Link */}
              <div className="mt-3 pt-3 border-t border-gray-700">
                <span className="text-xs text-purple-400 group-hover:text-purple-300 transition-colors flex items-center gap-1">
                  View Live Updates
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </Link>
          )
        })}
      </div>

      {/* View All Link */}
      {maxGames && liveGames.length >= maxGames && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <Link
            href="/live"
            className="block text-center text-sm text-purple-400 hover:text-purple-300 transition-colors"
          >
            View All Live Games →
          </Link>
        </div>
      )}
    </div>
  )
}
