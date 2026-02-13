'use client'

import { useState } from 'react'
import { usePredictions, useAccuracy } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { formatGameTime, formatOdds, formatSpread } from '@/lib/utils/format'
import { BarChart3, ChevronDown, ChevronUp, DollarSign, Users } from 'lucide-react'
import type { GamePrediction } from '@/lib/api/schemas'

export default function EnsemblePredictionsPage() {
  const { data, isLoading, error, refetch } = usePredictions()
  const { data: accuracyData } = useAccuracy()
  const [expandedGame, setExpandedGame] = useState<string | null>(null)

  const predictions = data?.predictions || []
  const avgConfidence = predictions.length
    ? Math.round(predictions.reduce((acc, p) => acc + p.confidence, 0) / predictions.length)
    : 0

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <h1 className="text-2xl font-bold tracking-tight">Ensemble Consensus</h1>
          <p className="text-muted-foreground">Model agreement + betting edges from the three-model voting system.</p>
        </div>
      </header>

      <div className="container-wide py-8">
        {isLoading && <PageSkeleton />}
        {error && <ErrorState message={error.message} retry={() => refetch()} />}

        {data && !isLoading && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Games" value={data.total_games || predictions.length} />
              <StatCard label="Avg Confidence" value={`${avgConfidence}%`} />
              <StatCard
                label="Model Accuracy"
                value={typeof accuracyData?.accuracy === 'number' ? `${accuracyData.accuracy}%` : '—'}
                accent
              />
              <StatCard label="Models" value={data.model_info?.num_models ?? '—'} />
            </div>

            {data.message && (
              <div className="bento-item mb-6 text-sm text-muted-foreground">
                {data.message}
              </div>
            )}

            {predictions.length === 0 && (
              <EmptyState
                title="No ensemble data yet"
                description="Run the daily pipeline to populate model votes and confidence bands."
                icon="predictions"
              />
            )}

            <div className="space-y-4">
              {predictions.map((prediction) => (
                <EnsembleCard
                  key={prediction.game_id}
                  prediction={prediction}
                  isExpanded={expandedGame === prediction.game_id}
                  onToggle={() =>
                    setExpandedGame(expandedGame === prediction.game_id ? null : prediction.game_id)
                  }
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="bento-item">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${accent ? 'text-secondary' : ''}`}>{value}</div>
    </div>
  )
}

function EnsembleCard({
  prediction,
  isExpanded,
  onToggle,
}: {
  prediction: GamePrediction
  isExpanded: boolean
  onToggle: () => void
}) {
  const isHomeWin = prediction.prediction === 'HOME_WIN'
  const winProb = isHomeWin ? prediction.home_win_probability : prediction.away_win_probability
  const consensus = prediction.consensus_percentage ?? prediction.confidence
  const votes = prediction.individual_votes || {}
  const modelCount = Object.keys(votes).length || (typeof prediction.models_agree === 'number' ? prediction.models_agree : undefined)

  return (
    <div className="bento-item overflow-hidden p-0">
      <button type="button" onClick={onToggle} className="w-full text-left p-5 card-interactive">
        <div className="flex items-center justify-between gap-4">
          <div className="w-24 shrink-0">
            <div className="text-xs font-mono text-muted-foreground">{formatGameTime(prediction.commence_time)}</div>
            <div className="text-xs text-muted-foreground">Consensus</div>
          </div>

          <div className="flex-1 grid grid-cols-3 items-center gap-2">
            <div className={`text-right ${isHomeWin ? 'font-semibold' : 'text-muted-foreground'}`}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Home</div>
              <div>{prediction.home_team}</div>
            </div>

            <div className="text-center">
              <div className="text-lg font-semibold tabular-nums">{consensus.toFixed(0)}%</div>
              <div className="mt-1 prob-bar">
                <div className="prob-bar-fill bg-foreground" style={{ width: `${prediction.home_win_probability}%` }} />
              </div>
            </div>

            <div className={`text-left ${!isHomeWin ? 'font-semibold' : 'text-muted-foreground'}`}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Away</div>
              <div>{prediction.away_team}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`badge ${winProb >= 65 ? 'badge-success' : winProb >= 55 ? 'badge-warning' : ''}`}>
              {winProb.toFixed(0)}%
            </span>
            <span className="text-xs text-muted-foreground">{modelCount ? `${modelCount} models` : '—'}</span>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-border p-5 bg-muted/30">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <Users className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Model Votes</h4>
              </div>
              <div className="space-y-1.5 text-sm">
                {Object.entries(votes).map(([model, vote]) => (
                  <div key={model} className="flex justify-between items-center">
                    <span className="text-muted-foreground">{model}</span>
                    <span className={vote === 'HOME' ? 'text-success font-medium' : 'font-medium'}>{vote}</span>
                  </div>
                ))}
                {Object.keys(votes).length === 0 && (
                  <p className="text-muted-foreground">Agreement: {prediction.models_agree ?? modelCount ?? '—'}</p>
                )}
              </div>
            </div>

            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Consensus Drivers</h4>
              </div>
              <div className="space-y-1.5 text-sm text-muted-foreground">
                <div>Pre-game form + rest advantage</div>
                <div>Home court edge baked in</div>
                <div>Chemistry delta stabilizes high-confidence picks</div>
              </div>
            </div>

            <div className="p-4 rounded-md border border-border">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">Betting Context</h4>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Spread</span>
                  <span className="font-mono">{formatSpread(prediction.home_spread ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Home Odds</span>
                  <span className="font-mono">{formatOdds(prediction.home_odds)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
