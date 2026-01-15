'use client'

import { useChemistry } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'

// NBA Team data - simplified colors for monochrome aesthetic
const NBA_TEAMS = [
    { abbr: 'ATL', name: 'Atlanta Hawks' },
    { abbr: 'BOS', name: 'Boston Celtics' },
    { abbr: 'BKN', name: 'Brooklyn Nets' },
    { abbr: 'CHA', name: 'Charlotte Hornets' },
    { abbr: 'CHI', name: 'Chicago Bulls' },
    { abbr: 'CLE', name: 'Cleveland Cavaliers' },
    { abbr: 'DAL', name: 'Dallas Mavericks' },
    { abbr: 'DEN', name: 'Denver Nuggets' },
    { abbr: 'DET', name: 'Detroit Pistons' },
    { abbr: 'GSW', name: 'Golden State Warriors' },
    { abbr: 'HOU', name: 'Houston Rockets' },
    { abbr: 'IND', name: 'Indiana Pacers' },
    { abbr: 'LAC', name: 'Los Angeles Clippers' },
    { abbr: 'LAL', name: 'Los Angeles Lakers' },
    { abbr: 'MEM', name: 'Memphis Grizzlies' },
    { abbr: 'MIA', name: 'Miami Heat' },
    { abbr: 'MIL', name: 'Milwaukee Bucks' },
    { abbr: 'MIN', name: 'Minnesota Timberwolves' },
    { abbr: 'NOP', name: 'New Orleans Pelicans' },
    { abbr: 'NYK', name: 'New York Knicks' },
    { abbr: 'OKC', name: 'Oklahoma City Thunder' },
    { abbr: 'ORL', name: 'Orlando Magic' },
    { abbr: 'PHI', name: 'Philadelphia 76ers' },
    { abbr: 'PHX', name: 'Phoenix Suns' },
    { abbr: 'POR', name: 'Portland Trail Blazers' },
    { abbr: 'SAC', name: 'Sacramento Kings' },
    { abbr: 'SAS', name: 'San Antonio Spurs' },
    { abbr: 'TOR', name: 'Toronto Raptors' },
    { abbr: 'UTA', name: 'Utah Jazz' },
    { abbr: 'WAS', name: 'Washington Wizards' },
]

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
