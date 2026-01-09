'use client'

import Link from 'next/link'
import { ArrowRight, Brain, Calendar, FlaskConical, Target, TrendingUp, Zap } from 'lucide-react'
import { usePredictions } from '@/lib/hooks'
import { KPICard } from '@/components/shared/kpi-card'
import { PredictionCardSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { formatGameTime, getConfidenceBg, getConfidenceColor } from '@/lib/utils/format'

export default function HomePage() {
  const { data, isLoading, error, refetch } = usePredictions()

  const topPicks = data?.predictions.slice(0, 6) || []
  const highConfidence = data?.predictions.filter(p => p.confidence >= 70).length || 0

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-purple-900/20 via-background to-pink-900/10 border-b border-border">
        <div className="absolute inset-0 bg-grid-white/5 [mask-image:linear-gradient(0deg,transparent,white)]" />
        <div className="container mx-auto px-6 py-16 relative">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-4">
              <Zap className="h-4 w-4" />
              Powered by 3 ML Models
            </div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
              NBA Game Predictions with{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                Machine Learning
              </span>
            </h1>
            <p className="text-lg text-muted-foreground mb-6">
              XGBoost, LightGBM, and CatBoost ensemble model with player chemistry analysis,
              SHAP explanations, and Kelly Criterion betting suggestions.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/predictions"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
              >
                View All Predictions
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/analytics"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                Model Analytics
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* KPI Stats */}
      <section className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            title="Games Today"
            value={data?.total_games || 0}
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
            title="Models Voting"
            value="3"
            icon={Brain}
            valueClassName="text-purple-400"
          />
          <KPICard
            title="Model Accuracy"
            value="67.7%"
            icon={TrendingUp}
            valueClassName="text-secondary"
          />
        </div>
      </section>

      {/* Today's Top Picks */}
      <section className="container mx-auto px-6 pb-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Today's Predictions</h2>
            <p className="text-sm text-muted-foreground">Latest ensemble model predictions</p>
          </div>
          <Link
            href="/predictions"
            className="text-sm text-primary hover:underline flex items-center gap-1"
          >
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {isLoading && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <PredictionCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <ErrorState
            message={error.message}
            retry={() => refetch()}
          />
        )}

        {data && !isLoading && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topPicks.map((pred) => (
              <Link
                key={pred.game_id}
                href="/predictions"
                className="block rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-all group"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs text-muted-foreground">
                    {formatGameTime(pred.commence_time)}
                  </span>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full border ${getConfidenceBg(pred.confidence)} ${getConfidenceColor(pred.confidence)}`}>
                    {pred.confidence.toFixed(0)}% conf
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Home Team */}
                  <div className={`flex-1 p-3 rounded-lg border ${pred.prediction === 'HOME_WIN' ? 'bg-green-500/10 border-green-500/30' : 'bg-muted/50 border-border'}`}>
                    <div className="text-xs text-muted-foreground">HOME</div>
                    <div className="font-bold">{pred.home_team}</div>
                    <div className={`text-xl font-black ${pred.prediction === 'HOME_WIN' ? 'text-green-400' : 'text-muted-foreground'}`}>
                      {pred.home_win_probability.toFixed(0)}%
                    </div>
                  </div>

                  <span className="text-muted-foreground font-bold">vs</span>

                  {/* Away Team */}
                  <div className={`flex-1 p-3 rounded-lg border ${pred.prediction === 'AWAY_WIN' ? 'bg-green-500/10 border-green-500/30' : 'bg-muted/50 border-border'}`}>
                    <div className="text-xs text-muted-foreground">AWAY</div>
                    <div className="font-bold">{pred.away_team}</div>
                    <div className={`text-xl font-black ${pred.prediction === 'AWAY_WIN' ? 'text-green-400' : 'text-muted-foreground'}`}>
                      {pred.away_win_probability.toFixed(0)}%
                    </div>
                  </div>
                </div>

                <div className="mt-3 text-xs text-muted-foreground group-hover:text-primary transition-colors">
                  Click for details →
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-6 pb-16">
        <h2 className="text-2xl font-bold mb-6">Platform Features</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl border border-border bg-card">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4">
              <Brain className="h-6 w-6 text-purple-400" />
            </div>
            <h3 className="font-bold mb-2">Ensemble ML</h3>
            <p className="text-sm text-muted-foreground">
              XGBoost, LightGBM, and CatBoost voting together for robust predictions
            </p>
          </div>
          <div className="p-6 rounded-xl border border-border bg-card">
            <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center mb-4">
              <FlaskConical className="h-6 w-6 text-green-400" />
            </div>
            <h3 className="font-bold mb-2">Chemistry GNN</h3>
            <p className="text-sm text-muted-foreground">
              Player synergy analysis from 5,498 duo combinations
            </p>
          </div>
          <div className="p-6 rounded-xl border border-border bg-card">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="font-bold mb-2">Explainable AI</h3>
            <p className="text-sm text-muted-foreground">
              SHAP values show exactly why each prediction was made
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
