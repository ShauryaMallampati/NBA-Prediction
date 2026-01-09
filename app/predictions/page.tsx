'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { usePredictions } from '@/lib/hooks'
import { KPICard } from '@/components/shared/kpi-card'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { formatGameTime, getConfidenceBg, getConfidenceColor, formatSpread } from '@/lib/utils/format'
import { Brain, Calendar, ChevronDown, ChevronUp, DollarSign, Home, Target, TrendingUp, Zap } from 'lucide-react'
import type { GamePrediction } from '@/lib/api/schemas'

export default function PredictionsPage() {
  const { data, isLoading, error, refetch, isFetching } = usePredictions()
  const [expandedGame, setExpandedGame] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'time' | 'confidence'>('time')

  const predictions = data?.predictions || []
  const sortedPredictions = [...predictions].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence
    return new Date(a.commence_time).getTime() - new Date(b.commence_time).getTime()
  })

  const highConfidence = predictions.filter(p => p.confidence >= 70).length
  const avgConfidence = predictions.length > 0
    ? (predictions.reduce((acc, p) => acc + p.confidence, 0) / predictions.length).toFixed(1)
    : '0'

  const calculateKellyBet = (prob: number, odds: number) => {
    if (!odds || odds <= 0) return 0
    const decimalOdds = odds > 0 ? odds / 100 + 1 : 100 / Math.abs(odds) + 1
    const kellyFraction = (prob * decimalOdds - 1) / (decimalOdds - 1)
    const quarterKelly = kellyFraction * 0.25
    return Math.max(0, Math.min(0.05, quarterKelly)) * 100
  }

  return (
    <div className="min-h-screen">
      <Header
        title="Predictions"
        description="Ensemble model predictions for upcoming games"
        showRefresh
        isRefreshing={isFetching}
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
                title="Total Games"
                value={data.total_games}
                icon={Calendar}
                valueClassName="text-primary"
              />
              <KPICard
                title="High Confidence"
                value={highConfidence}
                icon={Target}
                valueClassName="text-green-400"
              />
              <KPICard
                title="Avg Confidence"
                value={`${avgConfidence}%`}
                icon={TrendingUp}
              />
              <KPICard
                title="Models Voting"
                value="3/3"
                icon={Brain}
                valueClassName="text-purple-400"
              />
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
              <span className="text-sm text-muted-foreground">Sort by:</span>
              <button
                onClick={() => setSortBy('time')}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${sortBy === 'time' ? 'bg-primary text-primary-foreground' : 'border-border hover:bg-accent'
                  }`}
              >
                Game Time
              </button>
              <button
                onClick={() => setSortBy('confidence')}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${sortBy === 'confidence' ? 'bg-primary text-primary-foreground' : 'border-border hover:bg-accent'
                  }`}
              >
                Confidence
              </button>
            </div>

            {/* Empty State */}
            {predictions.length === 0 && (
              <EmptyState
                title="No Predictions Available"
                description="There are no games with predictions at this time."
                icon="predictions"
              />
            )}

            {/* Predictions List */}
            <div className="space-y-4">
              {sortedPredictions.map((pred) => (
                <PredictionCard
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

interface PredictionCardProps {
  prediction: GamePrediction
  isExpanded: boolean
  onToggle: () => void
  calculateKellyBet: (prob: number, odds: number) => number
}

function PredictionCard({ prediction: pred, isExpanded, onToggle, calculateKellyBet }: PredictionCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card hover:border-primary/30 transition-all overflow-hidden">
      {/* Main Row */}
      <div className="p-6 cursor-pointer" onClick={onToggle}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Teams */}
          <div className="flex-1">
            <div className="text-xs text-muted-foreground mb-3">
              {formatGameTime(pred.commence_time)}
            </div>
            <div className="flex items-center gap-4">
              {/* Home Team */}
              <div className={`flex-1 p-4 rounded-lg border-2 ${pred.prediction === 'HOME_WIN'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-muted/30 border-border'
                }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <Home className="h-3 w-3" /> HOME
                    </div>
                    <div className="font-bold text-lg">{pred.home_team}</div>
                  </div>
                  <div className={`text-3xl font-black ${pred.prediction === 'HOME_WIN' ? 'text-green-400' : 'text-muted-foreground'
                    }`}>
                    {pred.home_win_probability.toFixed(0)}%
                  </div>
                </div>
              </div>

              <span className="text-muted-foreground font-bold">VS</span>

              {/* Away Team */}
              <div className={`flex-1 p-4 rounded-lg border-2 ${pred.prediction === 'AWAY_WIN'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-muted/30 border-border'
                }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-muted-foreground">AWAY</div>
                    <div className="font-bold text-lg">{pred.away_team}</div>
                  </div>
                  <div className={`text-3xl font-black ${pred.prediction === 'AWAY_WIN' ? 'text-green-400' : 'text-muted-foreground'
                    }`}>
                    {pred.away_win_probability.toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-xl border font-bold ${getConfidenceBg(pred.confidence)} ${getConfidenceColor(pred.confidence)}`}>
              {pred.confidence.toFixed(0)}% Probability
            </div>
            <div className="p-2 rounded-lg hover:bg-accent transition-colors">
              {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-border p-6 bg-gradient-to-b from-transparent to-primary/5">
          <div className="grid md:grid-cols-3 gap-6">
            {/* Model Votes */}
            <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="h-5 w-5 text-purple-400" />
                <h4 className="font-bold text-purple-300">Model Votes</h4>
              </div>
              <div className="space-y-2 text-sm">
                {Object.entries(pred.individual_votes || {}).map(([model, vote]) => (
                  <div key={model} className="flex justify-between items-center">
                    <span className="text-muted-foreground capitalize">{model}</span>
                    <span className={vote === 'HOME' ? 'text-green-400 font-bold' : 'text-blue-400 font-bold'}>
                      {vote}
                    </span>
                  </div>
                ))}
                {Object.keys(pred.individual_votes || {}).length === 0 && (
                  <p className="text-muted-foreground">Agreement: {pred.models_agree}</p>
                )}
              </div>
            </div>

            {/* XAI Explanation */}
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="h-5 w-5 text-blue-400" />
                <h4 className="font-bold text-blue-300">Why This Prediction?</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-green-400">
                  <TrendingUp className="h-4 w-4" />
                  <span>Elo Advantage</span>
                </div>
                <div className="flex items-center gap-2 text-green-400">
                  <TrendingUp className="h-4 w-4" />
                  <span>Home Court</span>
                </div>
                <div className="flex items-center gap-2 text-yellow-400">
                  <TrendingUp className="h-4 w-4" />
                  <span>Chemistry Impact</span>
                </div>
              </div>
            </div>

            {/* Kelly Criterion */}
            <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="h-5 w-5 text-green-400" />
                <h4 className="font-bold text-green-300">Betting Suggestion</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Quarter Kelly</span>
                  <span className="text-green-400 font-bold">
                    {calculateKellyBet(pred.home_win_probability / 100, pred.home_odds || -110).toFixed(1)}% of bankroll
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Spread</span>
                  <span className="font-bold">{formatSpread(pred.home_spread)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Home Odds</span>
                  <span className="font-bold">{pred.home_odds > 0 ? '+' : ''}{pred.home_odds}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
