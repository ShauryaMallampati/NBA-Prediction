'use client'

import { useChemistry } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { FlaskConical, Medal, Users } from 'lucide-react'

export default function ChemistryPage() {
  const { data, isLoading, error, refetch } = useChemistry()

  return (
    <div className="min-h-screen">
      {/* Page header */}
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <h1 className="text-2xl font-bold tracking-tight">Player Chemistry</h1>
          <p className="text-muted-foreground">Team synergy analysis from lineup data using GNN embeddings</p>
        </div>
      </header>

      <div className="container-wide py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState message={error.message} retry={() => refetch()} />
        )}

        {data && !isLoading && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              <StatCard label="Teams" value={data.total_teams} icon={Users} />
              <StatCard label="Player Pairs" value={data.total_pairs.toLocaleString()} icon={FlaskConical} />
              <StatCard
                label="Top Net Rating"
                value={data.top_duos[0]?.net_rating ? `+${data.top_duos[0].net_rating.toFixed(1)}` : '—'}
              />
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Top duos */}
              <section className="bento-item">
                <div className="flex items-center gap-2 mb-6">
                  <FlaskConical className="h-5 w-5 text-muted-foreground" />
                  <h2 className="font-semibold">Top Player Duos</h2>
                </div>
                <div className="space-y-2">
                  {data.top_duos.slice(0, 10).map((duo, i) => (
                    <div
                      key={duo.players}
                      className="flex items-center gap-3 p-3 rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <div className="w-7 h-7 rounded-md bg-muted flex items-center justify-center font-mono text-xs text-muted-foreground">
                        {String(i + 1).padStart(2, '0')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{duo.players}</div>
                        <div className="text-xs text-muted-foreground">{duo.team} · {duo.games} games</div>
                      </div>
                      <div className={`font-mono font-semibold ${duo.net_rating > 0 ? 'text-success' : 'text-destructive'}`}>
                        {duo.net_rating > 0 ? '+' : ''}{duo.net_rating.toFixed(1)}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Team rankings */}
              <section className="bento-item">
                <div className="flex items-center gap-2 mb-6">
                  <Medal className="h-5 w-5 text-muted-foreground" />
                  <h2 className="font-semibold">Team Chemistry Rankings</h2>
                </div>
                <div className="space-y-2">
                  {data.team_rankings.slice(0, 15).map((team, i) => (
                    <div
                      key={team.team}
                      className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/30 transition-colors"
                    >
                      <div className="w-7 h-7 rounded-md bg-muted flex items-center justify-center font-mono text-xs text-muted-foreground">
                        {String(i + 1).padStart(2, '0')}
                      </div>
                      <div className="flex-1 font-medium text-sm">{team.team}</div>
                      <div className="flex items-center gap-2">
                        <div className="w-20 prob-bar">
                          <div
                            className="prob-bar-fill bg-foreground"
                            style={{ width: `${team.chemistry_score * 100}%` }}
                          />
                        </div>
                        <span className="w-8 text-xs text-right font-mono">
                          {(team.chemistry_score * 100).toFixed(0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// --- Components ---

function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon?: React.ElementType }) {
  return (
    <div className="bento-item">
      <div className="flex items-center gap-2 mb-2">
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
        <div className="stat-label">{label}</div>
      </div>
      <div className="stat-value">{value}</div>
    </div>
  )
}
