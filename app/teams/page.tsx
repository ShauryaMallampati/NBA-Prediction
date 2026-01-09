'use client'

import { Header } from '@/components/layout/header'
import { useChemistry } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { Users } from 'lucide-react'

// NBA Team data with colors
const NBA_TEAMS = [
    { abbr: 'ATL', name: 'Atlanta Hawks', color: 'bg-red-500' },
    { abbr: 'BOS', name: 'Boston Celtics', color: 'bg-green-600' },
    { abbr: 'BKN', name: 'Brooklyn Nets', color: 'bg-gray-800' },
    { abbr: 'CHA', name: 'Charlotte Hornets', color: 'bg-teal-500' },
    { abbr: 'CHI', name: 'Chicago Bulls', color: 'bg-red-600' },
    { abbr: 'CLE', name: 'Cleveland Cavaliers', color: 'bg-red-800' },
    { abbr: 'DAL', name: 'Dallas Mavericks', color: 'bg-blue-600' },
    { abbr: 'DEN', name: 'Denver Nuggets', color: 'bg-yellow-500' },
    { abbr: 'DET', name: 'Detroit Pistons', color: 'bg-red-500' },
    { abbr: 'GSW', name: 'Golden State Warriors', color: 'bg-blue-500' },
    { abbr: 'HOU', name: 'Houston Rockets', color: 'bg-red-600' },
    { abbr: 'IND', name: 'Indiana Pacers', color: 'bg-yellow-400' },
    { abbr: 'LAC', name: 'Los Angeles Clippers', color: 'bg-red-500' },
    { abbr: 'LAL', name: 'Los Angeles Lakers', color: 'bg-purple-600' },
    { abbr: 'MEM', name: 'Memphis Grizzlies', color: 'bg-blue-700' },
    { abbr: 'MIA', name: 'Miami Heat', color: 'bg-red-600' },
    { abbr: 'MIL', name: 'Milwaukee Bucks', color: 'bg-green-700' },
    { abbr: 'MIN', name: 'Minnesota Timberwolves', color: 'bg-blue-800' },
    { abbr: 'NOP', name: 'New Orleans Pelicans', color: 'bg-blue-600' },
    { abbr: 'NYK', name: 'New York Knicks', color: 'bg-orange-500' },
    { abbr: 'OKC', name: 'Oklahoma City Thunder', color: 'bg-blue-500' },
    { abbr: 'ORL', name: 'Orlando Magic', color: 'bg-blue-600' },
    { abbr: 'PHI', name: 'Philadelphia 76ers', color: 'bg-blue-700' },
    { abbr: 'PHX', name: 'Phoenix Suns', color: 'bg-purple-500' },
    { abbr: 'POR', name: 'Portland Trail Blazers', color: 'bg-red-600' },
    { abbr: 'SAC', name: 'Sacramento Kings', color: 'bg-purple-700' },
    { abbr: 'SAS', name: 'San Antonio Spurs', color: 'bg-gray-600' },
    { abbr: 'TOR', name: 'Toronto Raptors', color: 'bg-red-600' },
    { abbr: 'UTA', name: 'Utah Jazz', color: 'bg-yellow-500' },
    { abbr: 'WAS', name: 'Washington Wizards', color: 'bg-blue-800' },
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
            <Header
                title="Teams"
                description="All 30 NBA teams with chemistry analysis"
            />

            <div className="container mx-auto px-6 py-8">
                {isLoading && <PageSkeleton />}

                {error && (
                    <ErrorState
                        message={error.message}
                        retry={() => refetch()}
                    />
                )}

                {!isLoading && !error && (
                    <>
                        <div className="mb-6 text-sm text-muted-foreground">
                            Showing all 30 NBA teams ranked by chemistry score
                        </div>

                        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            {teamsWithChemistry.map((team, i) => (
                                <div
                                    key={team.abbr}
                                    className="rounded-xl border border-border bg-card p-4 hover:border-primary/50 transition-all group"
                                >
                                    <div className="flex items-center gap-3 mb-3">
                                        <div className={`w-10 h-10 rounded-lg ${team.color} flex items-center justify-center text-white font-bold text-xs`}>
                                            {team.abbr}
                                        </div>
                                        <div className="min-w-0">
                                            <div className="font-bold text-sm truncate">{team.name}</div>
                                            <div className="text-xs text-muted-foreground">#{i + 1} Chemistry</div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Chemistry Score</span>
                                            <span className="font-medium">{(team.chemistry * 100).toFixed(0)}</span>
                                        </div>
                                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all"
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
