import { TrendingUp, TrendingDown, Activity } from "lucide-react"

interface PlayerStats {
  ppg: number
  apg: number
  rpg: number
  fg_pct: number
  fg3_pct: number
  ft_pct: number
  spg?: number
  bpg?: number
  tpg?: number
  mpg?: number
}

interface PlayerCardProps {
  playerId: number
  playerName: string
  teamAbbreviation: string
  stats: PlayerStats
  position?: string
  jerseyNumber?: string
  showDetailedStats?: boolean
  className?: string
}

export function PlayerCard({
  playerId,
  playerName,
  teamAbbreviation,
  stats,
  position,
  jerseyNumber,
  showDetailedStats = false,
  className = "",
}: PlayerCardProps) {
  const isHighScorer = stats.ppg >= 25
  const isEfficientShooter = stats.fg_pct >= 50

  return (
    <div
      className={`glass-strong rounded-xl p-6 hover:bg-white/5 transition-all duration-200 group ${className}`}
    >
      {/* Player Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          {/* Avatar */}
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-xl">
            {jerseyNumber || teamAbbreviation.substring(0, 2)}
          </div>

          {/* Name and Team */}
          <div>
            <h3 className="text-xl font-bold text-white group-hover:text-purple-400 transition-colors">
              {playerName}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-gray-400">{teamAbbreviation}</span>
              {position && (
                <>
                  <span className="text-gray-600">•</span>
                  <span className="text-sm text-gray-400">{position}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-col gap-2">
          {isHighScorer && (
            <span className="px-2 py-1 rounded-full text-xs font-semibold bg-orange-500/20 text-orange-400 border border-orange-500/30">
              🔥 High Scorer
            </span>
          )}
          {isEfficientShooter && (
            <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
              ✨ Efficient
            </span>
          )}
        </div>
      </div>

      {/* Primary Stats Grid */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.ppg.toFixed(1)}</p>
          <p className="text-xs text-gray-500 mt-1">PPG</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.rpg.toFixed(1)}</p>
          <p className="text-xs text-gray-500 mt-1">RPG</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.apg.toFixed(1)}</p>
          <p className="text-xs text-gray-500 mt-1">APG</p>
        </div>
      </div>

      {/* Shooting Percentages */}
      <div className="space-y-2 mb-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">FG%</span>
            <span className="text-white font-medium">{stats.fg_pct.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
              style={{ width: `${Math.min(stats.fg_pct, 100)}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">3P%</span>
            <span className="text-white font-medium">{stats.fg3_pct.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
              style={{ width: `${Math.min(stats.fg3_pct, 100)}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">FT%</span>
            <span className="text-white font-medium">{stats.ft_pct.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
              style={{ width: `${Math.min(stats.ft_pct, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Detailed Stats (Optional) */}
      {showDetailedStats && (
        <div className="pt-4 border-t border-gray-800">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {stats.spg !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">Steals</span>
                <span className="text-white font-medium">{stats.spg.toFixed(1)}</span>
              </div>
            )}
            {stats.bpg !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">Blocks</span>
                <span className="text-white font-medium">{stats.bpg.toFixed(1)}</span>
              </div>
            )}
            {stats.tpg !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">Turnovers</span>
                <span className="text-white font-medium">{stats.tpg.toFixed(1)}</span>
              </div>
            )}
            {stats.mpg !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">Minutes</span>
                <span className="text-white font-medium">{stats.mpg.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* View Details Link */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <a
          href={`/players/${playerId}`}
          className="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-2 opacity-0 group-hover:opacity-100"
        >
          View Full Stats
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
    </div>
  )
}
