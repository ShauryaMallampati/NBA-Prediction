'use client'

import Link from 'next/link'
import { ArrowRight, BarChart3, Brain, Calendar, ChevronRight, Sparkles, Target, TrendingUp } from 'lucide-react'
import { usePredictions, useAccuracy } from '@/lib/hooks'
import { PredictionCardSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { formatGameTime } from '@/lib/utils/format'

export default function HomePage() {
  const { data, isLoading, error, refetch } = usePredictions()
  const { data: accuracyData } = useAccuracy()

  const topPicks = data?.predictions.slice(0, 6) || []
  const highConfidence = data?.predictions.filter(p => p.confidence >= 65).length || 0
  const avgConfidence = data?.predictions.length
    ? Math.round(data.predictions.reduce((a, p) => a + p.confidence, 0) / data.predictions.length)
    : 0
  const modelAccuracy = accuracyData?.accuracy ?? 67.7

  return (
    <div className="min-h-screen">
      {/* Hero - Clean, editorial style */}
      <section className="border-b border-border">
        <div className="container-wide py-16 lg:py-24">
          <div className="max-w-3xl">
            {/* Subtle badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-xs font-medium uppercase tracking-wider text-muted-foreground border border-border rounded-full">
              <Sparkles className="h-3.5 w-3.5" />
              3 ML Models · Updated Daily
            </div>

            {/* Clean headline - no gradients */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              NBA Game Predictions<br />
              <span className="text-muted-foreground">Powered by Machine Learning</span>
            </h1>

            <p className="text-lg text-muted-foreground mb-8 max-w-2xl leading-relaxed">
              XGBoost, LightGBM, and CatBoost ensemble voting with player chemistry analysis
              and SHAP-powered explanations for every prediction.
            </p>

            {/* Clean CTAs */}
            <div className="flex flex-wrap gap-3">
              <Link href="/predictions" className="btn-primary">
                View Predictions
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/analytics" className="btn-secondary">
                Model Performance
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar - Swiss grid precision */}
      <section className="border-b border-border bg-muted/30">
        <div className="container-wide py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <div className="stat-value">{data?.total_games || '—'}</div>
              <div className="stat-label">Games Today</div>
            </div>
            <div>
              <div className="stat-value text-success">{highConfidence}</div>
              <div className="stat-label">High Confidence</div>
            </div>
            <div>
              <div className="stat-value">{avgConfidence || '—'}%</div>
              <div className="stat-label">Avg Probability</div>
            </div>
            <div>
              <div className="stat-value text-secondary">{modelAccuracy}%</div>
              <div className="stat-label">Model Accuracy</div>
            </div>
          </div>
        </div>
      </section>

      {/* Today's Predictions - Bento Grid */}
      <section className="section-gap">
        <div className="container-wide">
          {/* Section header */}
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold mb-1">Today's Predictions</h2>
              <p className="text-muted-foreground">Ensemble model consensus for upcoming games</p>
            </div>
            <Link
              href="/predictions"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              View all <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <PredictionCardSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Error state */}
          {error && (
            <ErrorState message={error.message} retry={() => refetch()} />
          )}

          {/* Predictions grid */}
          {data && !isLoading && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topPicks.map((pred) => (
                <PredictionCard key={pred.game_id} prediction={pred} />
              ))}
            </div>
          )}

          {/* Empty state */}
          {data && !isLoading && topPicks.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No games scheduled today</p>
              <p className="text-sm">Check back tomorrow for new predictions</p>
            </div>
          )}
        </div>
      </section>

      {/* Features - Clean bento layout */}
      <section className="section-gap border-t border-border bg-muted/20">
        <div className="container-wide">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold mb-2">How It Works</h2>
            <p className="text-muted-foreground">Three-stage prediction pipeline</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <FeatureCard
              icon={Brain}
              number="01"
              title="Ensemble Learning"
              description="Three gradient boosting models vote together: XGBoost for precision, LightGBM for speed, CatBoost for robustness."
            />
            <FeatureCard
              icon={Target}
              number="02"
              title="Chemistry Analysis"
              description="Graph neural network analyzes 5,498 player duo combinations to capture team synergy and lineup dynamics."
            />
            <FeatureCard
              icon={BarChart3}
              number="03"
              title="SHAP Explanations"
              description="Every prediction includes feature importance breakdown so you understand exactly why we made the call."
            />
          </div>
        </div>
      </section>

      {/* Minimal footer CTA */}
      <section className="border-t border-border">
        <div className="container-wide py-16 text-center">
          <h3 className="text-xl font-bold mb-4">Ready to explore?</h3>
          <Link href="/predictions" className="btn-primary">
            View All Predictions
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  )
}

// ==============================================
// COMPONENTS
// ==============================================

interface Prediction {
  game_id: string
  home_team: string
  away_team: string
  home_win_probability: number
  away_win_probability: number
  prediction: string
  confidence: number
  commence_time: string
}

function PredictionCard({ prediction }: { prediction: Prediction }) {
  const isHomeWin = prediction.prediction === 'HOME_WIN'
  const winProb = isHomeWin ? prediction.home_win_probability : prediction.away_win_probability

  return (
    <Link
      href="/predictions"
      className="bento-item card-interactive group"
    >
      {/* Time + Confidence */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-muted-foreground font-mono">
          {formatGameTime(prediction.commence_time)}
        </span>
        <span className={`badge ${winProb >= 65 ? 'badge-success' : winProb >= 55 ? 'badge-warning' : ''}`}>
          {winProb.toFixed(0)}%
        </span>
      </div>

      {/* Teams */}
      <div className="space-y-3">
        {/* Home Team */}
        <div className={`flex items-center justify-between p-3 rounded-md border ${isHomeWin ? 'bg-success/5 border-success/20' : 'border-transparent'}`}>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">Home</div>
            <div className="font-semibold">{prediction.home_team}</div>
          </div>
          <div className={`text-2xl font-bold tabular-nums ${isHomeWin ? 'text-success' : 'text-muted-foreground'}`}>
            {prediction.home_win_probability.toFixed(0)}%
          </div>
        </div>

        {/* Away Team */}
        <div className={`flex items-center justify-between p-3 rounded-md border ${!isHomeWin ? 'bg-success/5 border-success/20' : 'border-transparent'}`}>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">Away</div>
            <div className="font-semibold">{prediction.away_team}</div>
          </div>
          <div className={`text-2xl font-bold tabular-nums ${!isHomeWin ? 'text-success' : 'text-muted-foreground'}`}>
            {prediction.away_win_probability.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Probability bar */}
      <div className="mt-4">
        <div className="prob-bar">
          <div
            className="prob-bar-fill bg-foreground"
            style={{ width: `${prediction.home_win_probability}%` }}
          />
        </div>
      </div>

      {/* Hover hint */}
      <div className="mt-3 text-xs text-muted-foreground group-hover:text-foreground transition-colors">
        View details →
      </div>
    </Link>
  )
}

function FeatureCard({
  icon: Icon,
  number,
  title,
  description
}: {
  icon: React.ElementType
  number: string
  title: string
  description: string
}) {
  return (
    <div className="bento-item">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <span className="text-xs font-mono text-muted-foreground">{number}</span>
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  )
}
