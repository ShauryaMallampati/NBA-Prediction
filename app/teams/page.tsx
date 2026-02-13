'use client'

import { useChemistry } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { NBA_TEAMS } from '@/lib/constants/teams'

export default function TeamsPage() {
    const { data, isLoading, error, refetch } = useChemistry()

    // Merge chemistry data with team info
    const teamsWithChemistry = NBA_TEAMS.map(team => {
        const chemData = data?.team_rankings.find(t => t.team === team.abbr)
        return {
            ...team,
            chemistry: chemData?.chemistry_score || 0,
        }
    }).sort((a, b) => b.chemistry - a.chemistry)

    return (
        <div className="min-h-screen">
            {/* Page Header */}
            <header className="border-b border-border">
                <div className="container-wide py-8">
                    <h1 className="text-2xl font-bold tracking-tight">Teams</h1>
                    <p className="text-muted-foreground">All 30 NBA teams ranked by chemistry score</p>
                </div>
            </header>

            <div className="container-wide py-8">
                {isLoading && <PageSkeleton />}

                {error && (
                    <ErrorState message={error.message} retry={() => refetch()} />
                )}

                {!isLoading && !error && (
                    <>
                        <div className="mb-6 text-sm text-muted-foreground">
                            Teams ranked by player synergy analysis from GNN model
                        </div>

                        {/* Teams Grid */}
                        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            {teamsWithChemistry.map((team, i) => (
                                <div
                                    key={team.abbr}
                                    className="bento-item card-interactive"
                                >
                                    <div className="flex items-center gap-3 mb-3">
                                        <div className="w-10 h-10 rounded-md bg-foreground flex items-center justify-center text-background font-bold text-xs">
                                            {team.abbr}
                                        </div>
                                        <div className="min-w-0">
                                            <div className="font-semibold text-sm truncate">{team.name}</div>
                                            <div className="text-xs text-muted-foreground font-mono">#{String(i + 1).padStart(2, '0')}</div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Chemistry</span>
                                            <span className="font-mono font-medium">{(team.chemistry * 100).toFixed(0)}</span>
                                        </div>
                                        <div className="prob-bar">
                                            <div
                                                className="prob-bar-fill bg-foreground"
                                                style={{ width: `${team.chemistry * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
