import { cn } from '@/lib/utils'

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
  className = '',
}: PlayerCardProps) {
  const isHighScorer = stats.ppg >= 25
  const isEfficientShooter = stats.fg_pct >= 50

  return (
    <div className={cn('bento-item card-interactive', className)}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-md bg-foreground text-background flex items-center justify-center font-semibold text-sm">
            {jerseyNumber || teamAbbreviation}
          </div>

          <div>
            <h3 className="text-lg font-semibold">{playerName}</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{teamAbbreviation}</span>
              {position && <span>• {position}</span>}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          {isHighScorer && <span className="badge badge-warning">High scorer</span>}
          {isEfficientShooter && <span className="badge badge-success">Efficient</span>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <p className="text-xl font-bold tabular-nums">{stats.ppg.toFixed(1)}</p>
          <p className="text-xs text-muted-foreground mt-1">PPG</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold tabular-nums">{stats.rpg.toFixed(1)}</p>
          <p className="text-xs text-muted-foreground mt-1">RPG</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold tabular-nums">{stats.apg.toFixed(1)}</p>
          <p className="text-xs text-muted-foreground mt-1">APG</p>
        </div>
      </div>

      <div className="space-y-3 mb-4">
        <StatBar label="FG%" value={stats.fg_pct} />
        <StatBar label="3P%" value={stats.fg3_pct} />
        <StatBar label="FT%" value={stats.ft_pct} />
      </div>

      {showDetailedStats && (
        <div className="pt-4 border-t border-border">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {stats.spg !== undefined && (
              <DetailRow label="Steals" value={stats.spg} />
            )}
            {stats.bpg !== undefined && (
              <DetailRow label="Blocks" value={stats.bpg} />
            )}
            {stats.tpg !== undefined && (
              <DetailRow label="Turnovers" value={stats.tpg} />
            )}
            {stats.mpg !== undefined && (
              <DetailRow label="Minutes" value={stats.mpg} />
            )}
          </div>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-border">
        <a
          href={`/players/${playerId}`}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-2"
        >
          View full stats
          <span className="text-xs">→</span>
        </a>
      </div>
    </div>
  )
}

function StatBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1 text-muted-foreground">
        <span>{label}</span>
        <span className="font-medium text-foreground">{value.toFixed(1)}%</span>
      </div>
      <div className="prob-bar">
        <div
          className="prob-bar-fill bg-foreground"
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between text-muted-foreground">
      <span>{label}</span>
      <span className="font-medium text-foreground">{value.toFixed(1)}</span>
    </div>
  )
}
