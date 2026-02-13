'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { MessageCircle } from 'lucide-react'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'

interface SentimentTrendPoint {
  date: string
  sentiment: number
}

interface TeamSentimentPoint {
  team: string
  sentiment: number
  change?: string
  posts?: number
}

interface SentimentResponse {
  success: boolean
  trend?: SentimentTrendPoint[]
  teams?: TeamSentimentPoint[]
  generated_at?: string
  message?: string
}

export default function SentimentPage() {
  const [data, setData] = useState<SentimentResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSentiment = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch('/api/sentiment')
        if (!response.ok) {
          const errorJson = await response.json().catch(() => null)
          throw new Error(errorJson?.message || 'Sentiment data unavailable')
        }
        const json = (await response.json()) as SentimentResponse
        if (!json.success) throw new Error(json.message || 'Sentiment data unavailable')
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    loadSentiment()
  }, [])

  const trend = data?.trend || []
  const teams = data?.teams || []

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <div className="flex items-center gap-3 mb-2">
            <MessageCircle className="h-6 w-6 text-muted-foreground" />
            <h1 className="text-2xl font-bold tracking-tight">Social Sentiment</h1>
          </div>
          <p className="text-muted-foreground">Live sentiment ingestion from social sources.</p>
        </div>
      </header>

      <div className="container-wide py-8 space-y-6">
        {loading && <PageSkeleton />}
        {error && <ErrorState message={error} />}

        {!loading && !error && data && trend.length === 0 && (
          <EmptyState
            title="No sentiment data yet"
            description={data.message || 'Run the sentiment ingestion pipeline to populate this view.'}
            icon="empty"
          />
        )}

        {!loading && !error && trend.length > 0 && (
          <>
            <div className="bento-item">
              <h2 className="text-lg font-semibold mb-4">Sentiment Trend (Last 7 Days)</h2>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" className="text-muted-foreground" />
                  <YAxis
                    className="text-muted-foreground"
                    domain={[0, 1]}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                    formatter={(value) => {
                      const numeric = typeof value === 'number' ? value : Number(value)
                      return Number.isFinite(numeric) ? `${(numeric * 100).toFixed(1)}%` : value
                    }}
                  />
                  <Line type="monotone" dataKey="sentiment" stroke="hsl(var(--primary))" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bento-item">
              <h2 className="text-lg font-semibold mb-6">Team Sentiment Rankings</h2>
              <div className="space-y-4">
                {teams.map((team, index) => (
                  <div key={team.team} className="p-4 rounded-md bg-muted/50 border border-border">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="text-lg font-semibold text-muted-foreground">#{index + 1}</span>
                          <span className="text-lg font-semibold">{team.team}</span>
                          {team.change && (
                            <span
                              className={`text-sm font-medium ${team.change.startsWith('+') ? 'text-success' : 'text-destructive'}`}
                            >
                              {team.change}
                            </span>
                          )}
                        </div>
                        {typeof team.posts === 'number' && (
                          <p className="text-sm text-muted-foreground">{team.posts.toLocaleString()} social posts analyzed</p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-secondary">{(team.sentiment * 100).toFixed(0)}</div>
                        <p className="text-sm text-muted-foreground">Sentiment</p>
                      </div>
                    </div>

                    <div className="h-2 bg-background rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-secondary to-primary transition-all"
                        style={{ width: `${team.sentiment * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
