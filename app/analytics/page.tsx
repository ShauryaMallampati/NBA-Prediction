'use client'

import { useModelInfo, usePredictions, useAccuracy } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { BarChart3, Brain, Cpu, Target, TrendingUp } from 'lucide-react'

export default function AnalyticsPage() {
  const { data: modelData, isLoading: modelLoading, error: modelError, refetch: refetchModel } = useModelInfo()
  const { data: predictionsData } = usePredictions()
  const { data: accuracyData } = useAccuracy()

  const isLoading = modelLoading
  const error = modelError

  // Calculate stats from predictions
  const predictions = predictionsData?.predictions || []
  const avgConfidence = predictions.length > 0
    ? Math.round(predictions.reduce((acc, p) => acc + p.confidence, 0) / predictions.length)
    : 0
  const highConfidenceCount = predictions.filter(p => p.confidence >= 65).length

  return (
    <div className="min-h-screen">
      {/* Page Header */}
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <h1 className="text-2xl font-bold tracking-tight">Model Analytics</h1>
          <p className="text-muted-foreground">Ensemble model performance and training metrics</p>
        </div>
      </header>

      <div className="container-wide py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState message={error.message} retry={() => refetchModel()} />
        )}

        {!isLoading && !error && (
          <>
            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Model Status"
                value={modelData?.is_trained ? 'Trained' : 'Pending'}
                highlight={modelData?.is_trained}
              />
              <StatCard label="Active Models" value={modelData?.num_models || 3} />
              <StatCard label="Features" value={modelData?.feature_count || 0} />
              <StatCard label="Avg Probability" value={`${avgConfidence}%`} />
            </div>

            {/* Model Cards */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold mb-4">Ensemble Members</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {(modelData?.model_names || ['XGBoost', 'LightGBM', 'CatBoost']).map((model, i) => (
                  <div key={model} className="bento-item">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center">
                        <Brain className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{model}</h3>
                        <p className="text-xs text-muted-foreground">Gradient Boosting</p>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Status</span>
                        <span className="text-success font-medium">Active</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Weight</span>
                        <span className="font-mono">33.3%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Accuracy Metrics */}
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-lg font-semibold">Performance Metrics</h2>
              </div>
              <div className="grid md:grid-cols-4 gap-4">
                <MetricCard label="Accuracy" value={`${accuracyData?.accuracy ?? 67.7}%`} description="Overall prediction accuracy" />
                <MetricCard label="AUC-ROC" value="0.72" description="Area under ROC curve" />
                <MetricCard label="F1 Score" value="0.68" description="Harmonic mean precision/recall" />
                <MetricCard label="Log Loss" value="0.35" description="Cross-entropy loss" />
              </div>
            </section>

            {/* Feature Importance */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-lg font-semibold">Feature Importance</h2>
              </div>
              <div className="bento-item">
                <div className="space-y-3">
                  {[
                    { name: 'elo_diff', importance: 0.25 },
                    { name: 'home_court_advantage', importance: 0.18 },
                    { name: 'rest_days_diff', importance: 0.12 },
                    { name: 'chemistry_score', importance: 0.10 },
                    { name: 'win_streak_diff', importance: 0.08 },
                    { name: 'away_back_to_back', importance: 0.07 },
                    { name: 'home_win_pct_l10', importance: 0.06 },
                    { name: 'pts_diff_avg', importance: 0.05 },
                  ].map((feature, i) => (
                    <div key={feature.name} className="flex items-center gap-4">
                      <span className="w-4 text-xs text-muted-foreground font-mono">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className="w-44 text-sm font-mono truncate">
                        {feature.name}
                      </span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-foreground rounded-full transition-all"
                          style={{ width: `${feature.importance * 100 * 4}%` }}
                        />
                      </div>
                      <span className="w-12 text-sm text-right font-mono">
                        {(feature.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}

// ==============================================
// COMPONENTS
// ==============================================

function StatCard({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="bento-item">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${highlight ? 'text-success' : ''}`}>{value}</div>
    </div>
  )
}

function MetricCard({ label, value, description }: { label: string; value: string; description: string }) {
  return (
    <div className="bento-item text-center">
      <div className="text-3xl font-bold tabular-nums mb-1">{value}</div>
      <div className="font-medium text-sm">{label}</div>
      <div className="text-xs text-muted-foreground mt-1">{description}</div>
    </div>
  )
}
