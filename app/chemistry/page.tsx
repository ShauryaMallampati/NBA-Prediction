'use client'

import { Header } from '@/components/layout/header'
import { useChemistry } from '@/lib/hooks'
import { KPICard } from '@/components/shared/kpi-card'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { FlaskConical, Medal, TrendingUp, Users } from 'lucide-react'

export default function ChemistryPage() {
  const { data, isLoading, error, refetch } = useChemistry()

  return (
    <div className="min-h-screen">
      <Header
        title="Player Chemistry"
        description="Team synergy analysis from lineup data"
      />

      <div className="container mx-auto px-6 py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState
            message={error.message}
            retry={() => refetch()}
          />
        )}

        {data && !isLoading && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <KPICard
                title="Teams Analyzed"
                value={data.total_teams}
                icon={Users}
                valueClassName="text-primary"
              />
              <KPICard
                title="Player Pairs"
                value={data.total_pairs.toLocaleString()}
                icon={FlaskConical}
                valueClassName="text-green-400"
              />
              <KPICard
                title="Top Rating"
                value={data.top_duos[0]?.net_rating?.toFixed(1) || 'N/A'}
                icon={TrendingUp}
                valueClassName="text-purple-400"
              />
              <KPICard
                title="Data Source"
                value="NBA API"
                icon={Medal}
              />
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
              {/* Top Duos */}
              <div className="rounded-xl border border-border bg-card p-6">
                <div className="flex items-center gap-2 mb-6">
                  <FlaskConical className="h-5 w-5 text-green-400" />
                  <h2 className="text-lg font-bold">Top Player Duos</h2>
                </div>
                <div className="space-y-3">
                  {data.top_duos.slice(0, 10).map((duo, i) => (
                    <div
                      key={duo.players}
                      className="flex items-center gap-4 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${i < 3 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-muted text-muted-foreground'
                        }`}>
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{duo.players}</div>
                        <div className="text-xs text-muted-foreground">{duo.team}</div>
                      </div>
                      <div className="text-right">
                        <div className={`font-bold ${duo.net_rating > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {duo.net_rating > 0 ? '+' : ''}{duo.net_rating.toFixed(1)}
                        </div>
                        <div className="text-xs text-muted-foreground">{duo.games} games</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Team Rankings */}
              <div className="rounded-xl border border-border bg-card p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Medal className="h-5 w-5 text-purple-400" />
                  <h2 className="text-lg font-bold">Team Chemistry Rankings</h2>
                </div>
                <div className="space-y-2">
                  {data.team_rankings.slice(0, 15).map((team, i) => (
                    <div
                      key={team.team}
                      className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/30 transition-colors"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${i < 3 ? 'bg-green-500/20 text-green-400' : 'bg-muted/50 text-muted-foreground'
                        }`}>
                        {i + 1}
                      </div>
                      <div className="flex-1 font-medium">{team.team}</div>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                            style={{ width: `${team.chemistry_score * 100}%` }}
                          />
                        </div>
                        <span className="w-12 text-sm text-right">
                          {(team.chemistry_score * 100).toFixed(0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
