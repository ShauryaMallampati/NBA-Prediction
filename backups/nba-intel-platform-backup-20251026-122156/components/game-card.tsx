import Link from "next/link"

interface GameCardProps {
  gameId: string
  date: string
  homeTeam: string
  awayTeam: string
  homeWinProb: number
  awayWinProb: number
  status?: "scheduled" | "live" | "final"
  homeScore?: number
  awayScore?: number
}

export function GameCard({
  gameId,
  date,
  homeTeam,
  awayTeam,
  homeWinProb,
  awayWinProb,
  status = "scheduled",
  homeScore,
  awayScore,
}: GameCardProps) {
  return (
    <Link
      href={status === "live" ? `/live/${gameId}` : status === "final" ? `/postgame/${gameId}` : "#"}
      className="block p-6 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">{awayTeam}</span>
              {status !== "scheduled" && <span className="text-2xl font-bold">{awayScore}</span>}
            </div>
            <span className="text-muted-foreground">@</span>
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">{homeTeam}</span>
              {status !== "scheduled" && <span className="text-2xl font-bold">{homeScore}</span>}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-sm text-muted-foreground">{date}</p>
            {status === "live" && (
              <span className="px-2 py-1 text-xs font-medium bg-destructive/20 text-destructive rounded-full animate-pulse">
                LIVE
              </span>
            )}
            {status === "final" && (
              <span className="px-2 py-1 text-xs font-medium bg-muted text-muted-foreground rounded-full">FINAL</span>
            )}
          </div>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold text-primary">{(homeWinProb * 100).toFixed(1)}%</div>
          <p className="text-sm text-muted-foreground">Home Win Prob</p>
        </div>
      </div>

      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-primary transition-all" style={{ width: `${homeWinProb * 100}%` }} />
      </div>

      <div className="mt-3 flex justify-between text-xs text-muted-foreground">
        <span>
          {awayTeam}: {(awayWinProb * 100).toFixed(1)}%
        </span>
        <span>
          {homeTeam}: {(homeWinProb * 100).toFixed(1)}%
        </span>
      </div>
    </Link>
  )
}
