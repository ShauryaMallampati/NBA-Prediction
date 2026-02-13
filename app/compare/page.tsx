'use client'

import { useEffect, useMemo, useState } from 'react'
import { NBA_TEAMS } from '@/lib/constants/teams'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { BarChart3, Swords } from 'lucide-react'

interface TeamSplit {
  games_played: number
  wins: number
  losses: number
  win_pct: number
  avg_points_for: number
  avg_points_against: number
  net_rating: number
  last_game_date: string | null
  streak: number
}

interface TeamSummary {
  abbr: string
  name: string
  short_name: string
  chemistry_score: number | null
  season: TeamSplit
  recent: TeamSplit
}

interface HeadToHead {
  games_played: number
  teamA_wins: number
  teamB_wins: number
  last_game_date: string | null
  recent: {
    teamA_wins: number
    teamB_wins: number
    avg_margin: number
  }
}

interface CompareResponse {
  success: boolean
  as_of: string | null
  teamA: TeamSummary
  teamB: TeamSummary
  head_to_head: HeadToHead
  message?: string
}

export default function ComparePage() {
  const [teamA, setTeamA] = useState('LAL')
  const [teamB, setTeamB] = useState('GSW')
  const [refreshKey, setRefreshKey] = useState(0)
  const [data, setData] = useState<CompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const teamOptions = useMemo(() => NBA_TEAMS, [])

  useEffect(() => {
    const loadCompare = async () => {
      if (teamA === teamB) {
        setError('Pick two different teams to compare.')
        setData(null)
        return
      }

      setLoading(true)
      setError(null)
      try {
        const response = await fetch(`/api/teams/compare?teamA=${teamA}&teamB=${teamB}`)
        if (!response.ok) throw new Error('Failed to load team comparison')
        const json = (await response.json()) as CompareResponse
        if (!json.success) throw new Error(json.message || 'Comparison data unavailable')
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    loadCompare()
  }, [teamA, teamB, refreshKey])

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <div className="flex items-center gap-3 mb-2">
            <Swords className="h-6 w-6 text-muted-foreground" />
            <h1 className="text-2xl font-bold tracking-tight">Team Comparison</h1>
          </div>
          <p className="text-muted-foreground">
            Head-to-head context and recent form pulled from the historical game log.
          </p>
        </div>
      </header>

      <div className="container-wide py-8">
        <section className="bento-item mb-8">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm text-muted-foreground">Team A</label>
              <select
                className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={teamA}
                onChange={(event) => setTeamA(event.target.value)}
              >
                {teamOptions.map((team) => (
                  <option key={team.abbr} value={team.abbr}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Team B</label>
              <select
                className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={teamB}
                onChange={(event) => setTeamB(event.target.value)}
              >
                {teamOptions.map((team) => (
                  <option key={team.abbr} value={team.abbr}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {data?.as_of && (
            <div className="mt-4 text-xs text-muted-foreground">
              Stats refreshed through <span className="font-mono">{data.as_of}</span>
            </div>
          )}
        </section>

        {loading && <PageSkeleton />}
        {error && <ErrorState message={error} retry={() => setRefreshKey((value) => value + 1)} />}

        {!loading && !error && data && (
          <div className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <TeamCard team={data.teamA} accent="success" />
              <TeamCard team={data.teamB} accent="secondary" />
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
              <SplitCard title="Season Snapshot" splitA={data.teamA.season} splitB={data.teamB.season} />
              <SplitCard title="Last 10 Games" splitA={data.teamA.recent} splitB={data.teamB.recent} />
              <HeadToHeadCard headToHead={data.head_to_head} teamA={data.teamA} teamB={data.teamB} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TeamCard({ team, accent }: { team: TeamSummary; accent: 'success' | 'secondary' }) {
  const chemistry = team.chemistry_score !== null ? `${(team.chemistry_score * 100).toFixed(0)}%` : '—'
  const streak = formatStreak(team.recent.streak)

  return (
    <div className="bento-item">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-wider">{team.abbr}</div>
          <h2 className="text-xl font-semibold">{team.name}</h2>
        </div>
        <div className={`badge ${accent === 'success' ? 'badge-success' : 'badge-warning'}`}>
          Chemistry {chemistry}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="stat-label">Season Record</div>
          <div className="stat-value text-lg">{team.season.wins}-{team.season.losses}</div>
        </div>
        <div>
          <div className="stat-label">Current Streak</div>
          <div className="stat-value text-lg">{streak}</div>
        </div>
        <div>
          <div className="stat-label">Avg Points</div>
          <div className="text-lg font-semibold tabular-nums">
            {team.season.avg_points_for.toFixed(1)}
          </div>
        </div>
        <div>
          <div className="stat-label">Net Rating</div>
          <div className="text-lg font-semibold tabular-nums">
            {team.season.net_rating >= 0 ? '+' : ''}{team.season.net_rating.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  )
}

function SplitCard({ title, splitA, splitB }: { title: string; splitA: TeamSplit; splitB: TeamSplit }) {
  return (
    <div className="bento-item">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="h-4 w-4 text-muted-foreground" />
        <h3 className="font-semibold text-sm">{title}</h3>
      </div>
      <div className="space-y-3 text-sm">
        <SplitRow label="Win %" valueA={formatPct(splitA.win_pct)} valueB={formatPct(splitB.win_pct)} />
        <SplitRow label="Offense" valueA={splitA.avg_points_for.toFixed(1)} valueB={splitB.avg_points_for.toFixed(1)} />
        <SplitRow label="Defense" valueA={splitA.avg_points_against.toFixed(1)} valueB={splitB.avg_points_against.toFixed(1)} />
        <SplitRow label="Net" valueA={formatSigned(splitA.net_rating)} valueB={formatSigned(splitB.net_rating)} />
      </div>
    </div>
  )
}

function SplitRow({ label, valueA, valueB }: { label: string; valueA: string; valueB: string }) {
  return (
    <div className="flex items-center justify-between text-muted-foreground">
      <span>{label}</span>
      <span className="font-mono text-foreground">
        {valueA} / {valueB}
      </span>
    </div>
  )
}

function HeadToHeadCard({ headToHead, teamA, teamB }: { headToHead: HeadToHead; teamA: TeamSummary; teamB: TeamSummary }) {
  return (
    <div className="bento-item">
      <div className="text-sm font-semibold mb-3">Head-to-Head</div>
      <div className="space-y-2 text-sm text-muted-foreground">
        <div className="flex items-center justify-between">
          <span>All-time record</span>
          <span className="font-mono text-foreground">
            {teamA.abbr} {headToHead.teamA_wins} - {headToHead.teamB_wins} {teamB.abbr}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Recent (last 5)</span>
          <span className="font-mono text-foreground">
            {headToHead.recent.teamA_wins} - {headToHead.recent.teamB_wins}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Avg margin</span>
          <span className="font-mono text-foreground">
            {headToHead.recent.avg_margin >= 0 ? '+' : ''}{headToHead.recent.avg_margin}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Last meeting</span>
          <span className="font-mono text-foreground">{headToHead.last_game_date || '—'}</span>
        </div>
      </div>
    </div>
  )
}

function formatPct(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function formatSigned(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}`
}

function formatStreak(streak: number) {
  if (streak === 0) return '—'
  return `${streak > 0 ? 'W' : 'L'}${Math.abs(streak)}`
}
