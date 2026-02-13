'use client'

import { useState } from 'react'
import { usePredictions, useAccuracy } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { formatGameTime, formatOdds, formatSpread } from '@/lib/utils/format'
import { BarChart3, Calendar, ChevronDown, ChevronUp, DollarSign, TrendingUp } from 'lucide-react'
import type { GamePrediction } from '@/lib/api/schemas'

export default function PredictionsPage() {
  const { data, isLoading, error, refetch, isFetching } = usePredictions()
  const { data: accuracyData } = useAccuracy()
  const [expandedGame, setExpandedGame] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'time' | 'confidence'>('time')

  const predictions = data?.predictions || []
  const sortedPredictions = [...predictions].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence
    return new Date(a.commence_time).getTime() - new Date(b.commence_time).getTime()
  })

  const highConfidence = predictions.filter(p => p.confidence >= 65).length
  const avgConfidence = predictions.length > 0
    ? Math.round(predictions.reduce((acc, p) => acc + p.confidence, 0) / predictions.length)
    : 0

  const calculateKellyBet = (prob: number, odds?: number) => {
    if (typeof odds !== 'number' || odds === 0) return null
    const decimalOdds = odds > 0 ? odds / 100 + 1 : 100 / Math.abs(odds) + 1
    const kellyFraction = (prob * decimalOdds - 1) / (decimalOdds - 1)
    const quarterKelly = kellyFraction * 0.25
    return Math.max(0, Math.min(0.05, quarterKelly)) * 100
  }

  return (
    <div className="min-h-screen">
      {/* Page header */}
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Predictions</h1>
              <p className="text-muted-foreground">Ensemble model consensus for upcoming games</p>
            </div>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="btn-secondary text-sm"
            >
              {isFetching ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Total Games" value={data.total_games ?? predictions.length} />
              <StatCard label="High Confidence" value={highConfidence} highlight />
              <StatCard label="Avg Probability" value={`${avgConfidence}%`} />
              <StatCard
                label="Model Accuracy"
                value={typeof accuracyData?.accuracy === 'number' ? `${accuracyData.accuracy}%` : '—'}
                accent
              />
            </div>

            {data.message && (
              <div className="bento-item mb-6 text-sm text-muted-foreground">
                {data.message}
              </div>
            )}

            {/* Sort controls */}
            <div className="flex items-center gap-3 mb-6">
              <span className="text-sm text-muted-foreground">Sort:</span>
              <button
                onClick={() => setSortBy('time')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${sortBy === 'time'
                  ? 'bg-foreground text-background'
                  : 'border border-border hover:bg-accent'
                  }`}
              >
                Time
              </button>
              <button
                onClick={() => setSortBy('confidence')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${sortBy === 'confidence'
                  ? 'bg-foreground text-background'
                  : 'border border-border hover:bg-accent'
                  }`}
              >
                Confidence
              </button>
            </div>

            {/* Empty state */}
            {predictions.length === 0 && (
              <EmptyState
                title="No Predictions Available"
                description="Check back later for new predictions."
                icon="predictions"
              />
            )}

            {/* Predictions list */}
            <div className="space-y-3">
              {sortedPredictions.map((pred) => (
                <PredictionRow
                  key={pred.game_id}
                  prediction={pred}
                  isExpanded={expandedGame === pred.game_id}
                  onToggle={() => setExpandedGame(expandedGame === pred.game_id ? null : pred.game_id)}
                  calculateKellyBet={calculateKellyBet}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// --- Components ---

function StatCard({ label, value, highlight, accent }: { label: string; value: string | number; highlight?: boolean; accent?: boolean }) {
  return (
    <div className="bento-item">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${highlight ? 'text-success' : accent ? 'text-secondary' : ''}`}>
        {value}
      </div>
    </div>
  )
}

interface PredictionRowProps {
  prediction: GamePrediction
  isExpanded: boolean
  onToggle: () => void
  calculateKellyBet: (prob: number, odds?: number) => number | null
}

function PredictionRow({ prediction: pred, isExpanded, onToggle, calculateKellyBet }: PredictionRowProps) {
  const isHomeWin = pred.prediction === 'HOME_WIN'
  const winProb = isHomeWin ? pred.home_win_probability : pred.away_win_probability
  const kelly = calculateKellyBet(pred.home_win_probability / 100, pred.home_odds)

  return (
    <div className="bento-item overflow-hidden p-0">
      {/* Main row */}
      <div className="p-5 cursor-pointer card-interactive" onClick={onToggle}>
        <div className="flex items-center justify-between gap-4">
          {/* Time */}
          <div className="w-20 shrink-0">
            <div className="text-xs font-mono text-muted-foreground">
              {formatGameTime(pred.commence_time)}
            </div>
          </div>

          {/* Teams */}
          <div className="flex-1 grid grid-cols-3 items-center gap-2">
            {/* Home */}
            <div className={`text-right ${isHomeWin ? 'font-semibold' : 'text-muted-foreground'}`}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Home</div>
              <div>{pred.home_team}</div>
            </div>

            {/* Probabilities */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-2">
                <span className={`text-lg tabular-nums ${isHomeWin ? 'font-bold' : 'text-muted-foreground'}`}>
                  {pred.home_win_probability.toFixed(0)}
                </span>
                <span className="text-muted-foreground">–</span>
                <span className={`text-lg tabular-nums ${!isHomeWin ? 'font-bold' : 'text-muted-foreground'}`}>
                  {pred.away_win_probability.toFixed(0)}
                </span>
              </div>
              {/* Probability bar */}
              <div className="mt-1.5 prob-bar">
                <div
                  className="prob-bar-fill bg-foreground"
                  style={{ width: `${pred.home_win_probability}%` }}
                />
              </div>
            </div>

            {/* Away */}
            <div className={`text-left ${!isHomeWin ? 'font-semibold' : 'text-muted-foreground'}`}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Away</div>
              <div>{pred.away_team}</div>
            </div>
          </div>

          {/* Confidence + expand */}
          <div className="flex items-center gap-2">
            <span className={`badge ${winProb >= 65 ? 'badge-success' : winProb >= 55 ? 'badge-warning' : ''}`}>
              {winProb.toFixed(0)}%
            </span>
            <button className="p-1.5 rounded-md hover:bg-accent transition-colors">
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t border-border p-5 bg-muted/30">
          <div className="grid md:grid-cols-3 gap-4">
            {/* Model votes */}
            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Model Votes</h4>
              </div>
              <div className="space-y-1.5 text-sm">
                {Object.entries(pred.individual_votes || {}).map(([model, vote]) => (
                  <div key={model} className="flex justify-between items-center">
                    <span className="text-muted-foreground">{model}</span>
                    <span className={vote === 'HOME' ? 'text-success font-medium' : 'font-medium'}>
                      {vote}
                    </span>
                  </div>
                ))}
                {Object.keys(pred.individual_votes || {}).length === 0 && (
                  <p className="text-muted-foreground">Agreement: {pred.models_agree}</p>
                )}
              </div>
            </div>

            {/* Key factors */}
            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Key Factors</h4>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-success" />
                  <span>Elo Advantage</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-success" />
                  <span>Home Court</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-secondary" />
                  <span>Chemistry Impact</span>
                </div>
              </div>
            </div>

            {/* Betting info */}
            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Betting Info</h4>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Quarter Kelly</span>
                  <span className="font-medium">
                    {typeof kelly === 'number' ? `${kelly.toFixed(1)}%` : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Spread</span>
                  <span className="font-mono">{formatSpread(pred.home_spread ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Home Odds</span>
                  <span className="font-mono">{formatOdds(pred.home_odds)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
