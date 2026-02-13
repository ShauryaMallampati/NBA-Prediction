'use client'

import { Activity, Clock, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { useCallback, useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

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
  refreshInterval?: number // seconds
  maxGames?: number
  className?: string
}

export function LiveScoreboard({
  autoRefresh = true,
  refreshInterval = 30,
  maxGames,
  className = '',
}: LiveScoreboardProps) {
  const [liveGames, setLiveGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [backendAvailable, setBackendAvailable] = useState(true)

  const fetchLiveGames = useCallback(async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL
      if (!backendUrl) {
        setBackendAvailable(false)
        setLiveGames([])
        setLoading(false)
        return
      }

      const response = await fetch(`${backendUrl}/api/games/live`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()
      let games = data.games || []

      if (maxGames && games.length > maxGames) {
        games = games.slice(0, maxGames)
      }

      setLiveGames(games)
      setLastUpdate(new Date())
      setBackendAvailable(true)
    } catch (err) {
      console.error('Error fetching live games:', err)
      setBackendAvailable(false)
    } finally {
      setLoading(false)
    }
  }, [maxGames])

  useEffect(() => {
    fetchLiveGames()

    if (autoRefresh) {
      const interval = setInterval(fetchLiveGames, refreshInterval * 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval, fetchLiveGames])

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
      <div className={cn('bento-item', className)}>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-8 h-8 text-muted-foreground animate-spin" />
        </div>
      </div>
    )
  }

  if (!backendAvailable) {
    return (
      <div className={cn('bento-item', className)}>
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-5 h-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Live Games</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Live feed needs the FastAPI server running with <span className="font-mono">NEXT_PUBLIC_API_URL</span>.
        </p>
      </div>
    )
  }

  if (liveGames.length === 0) {
    return (
      <div className={cn('bento-item', className)}>
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-5 h-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Live Games</h3>
        </div>
        <p className="text-muted-foreground text-center py-6">No live games right now.</p>
        <Link href="/predictions" className="btn-secondary w-full text-center">
          View predictions
        </Link>
      </div>
    )
  }

  return (
    <div className={cn('bento-item', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-destructive" />
          <h3 className="text-lg font-semibold">Live Games</h3>
          <span className="badge badge-warning">{liveGames.length}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            {lastUpdate.toLocaleTimeString()}
          </div>
          <button onClick={fetchLiveGames} className="btn-ghost px-2 py-1">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {liveGames.map((game) => {
          const leadingTeam = getLeadingTeam(game)

          return (
            <Link
              key={game.game_id}
              href={`/live/${game.game_id}`}
              className="block p-4 rounded-md border border-border hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-destructive rounded-full animate-pulse" />
                  <span className="text-xs font-semibold text-destructive">
                    LIVE • {getQuarter(game.period)}
                  </span>
                </div>
                {game.time_remaining && (
                  <span className="text-xs text-muted-foreground font-mono">{game.time_remaining}</span>
                )}
              </div>

              <div className="space-y-2">
                <ScoreRow
                  label={game.visitor_team?.name}
                  abbr={game.visitor_team?.abbreviation}
                  score={game.visitor_team?.score || 0}
                  highlight={leadingTeam === 'away'}
                />
                <ScoreRow
                  label={game.home_team?.name}
                  abbr={game.home_team?.abbreviation}
                  score={game.home_team?.score || 0}
                  highlight={leadingTeam === 'home'}
                />
              </div>

              <div className="mt-3 pt-3 border-t border-border text-xs text-muted-foreground">
                View live updates →
              </div>
            </Link>
          )
        })}
      </div>

      {maxGames && liveGames.length >= maxGames && (
        <div className="mt-4 pt-4 border-t border-border">
          <Link href="/live" className="btn-secondary w-full text-center">
            View all live games
          </Link>
        </div>
      )}
    </div>
  )
}

function ScoreRow({ label, abbr, score, highlight }: { label: string; abbr: string; score: number; highlight: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-md bg-muted flex items-center justify-center text-xs font-semibold">
          {abbr}
        </div>
        <span className="text-sm">{label}</span>
      </div>
      <div className={cn('text-lg font-bold', highlight ? 'text-success' : 'text-foreground')}>
        {score}
      </div>
    </div>
  )
}
