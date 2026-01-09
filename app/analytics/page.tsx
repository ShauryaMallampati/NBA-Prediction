'use client'

import { Header } from '@/components/layout/header'
import { useModelInfo, usePredictions } from '@/lib/hooks'
import { KPICard } from '@/components/shared/kpi-card'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { BarChart3, Brain, Cpu, Target, TrendingUp, Zap } from 'lucide-react'

export default function AnalyticsPage() {
  const { data: modelData, isLoading: modelLoading, error: modelError, refetch: refetchModel } = useModelInfo()
  const { data: predictionsData } = usePredictions()

  const isLoading = modelLoading
  const error = modelError

  // Calculate stats from predictions
  const predictions = predictionsData?.predictions || []
  const avgConfidence = predictions.length > 0
    ? (predictions.reduce((acc, p) => acc + p.confidence, 0) / predictions.length).toFixed(1)
    : '0'
  const highConfidenceCount = predictions.filter(p => p.confidence >= 70).length

  return (
    <div className="min-h-screen">
      <Header
        title="Model Analytics"
        description="Ensemble model performance and insights"
      />

      <div className="container mx-auto px-6 py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState
            message={error.message}
            retry={() => refetchModel()}
          />
        )}

        {!isLoading && !error && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <KPICard
                title="Model Status"
                value={modelData?.is_trained ? 'Trained' : 'Not Trained'}
                icon={Brain}
                valueClassName={modelData?.is_trained ? 'text-green-400' : 'text-red-400'}
              />
              <KPICard
                title="Active Models"
                value={modelData?.num_models || 3}
                icon={Cpu}
                valueClassName="text-purple-400"
              />
              <KPICard
                title="Features Used"
                value={modelData?.feature_count || 0}
                icon={BarChart3}
              />
              <KPICard
                title="Avg Win Prob"
                value={`${avgConfidence}%`}
                icon={Target}
                valueClassName="text-primary"
              />
            </div>

            {/* Model Cards */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              {(modelData?.model_names || ['XGBoost', 'LightGBM', 'CatBoost']).map((model, i) => (
                <div key={model} className="rounded-xl border border-border bg-card p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${i === 0 ? 'bg-purple-500/10' : i === 1 ? 'bg-green-500/10' : 'bg-blue-500/10'
                      }`}>
                      <Brain className={`h-5 w-5 ${i === 0 ? 'text-purple-400' : i === 1 ? 'text-green-400' : 'text-blue-400'
                        }`} />
                    </div>
                    <div>
                      <h3 className="font-bold">{model}</h3>
                      <p className="text-xs text-muted-foreground">Gradient Boosting</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <span className="text-green-400 font-medium">Active</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Weight</span>
                      <span>33.3%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Accuracy Metrics */}
            {/* TODO: Connect to real metrics endpoint (currently using static placeholders) */}
            <div className="rounded-xl border border-border bg-card p-6 mb-8">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Model Accuracy Metrics</h2>
              </div>
              <div className="grid md:grid-cols-4 gap-6">
                <div className="text-center p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                  <div className="text-3xl font-black text-green-400">67.7%</div>
                  <div className="text-sm text-muted-foreground mt-1">Overall Accuracy</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                  <div className="text-3xl font-black text-blue-400">0.72</div>
                  <div className="text-sm text-muted-foreground mt-1">AUC-ROC Score</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                  <div className="text-3xl font-black text-purple-400">0.68</div>
                  <div className="text-sm text-muted-foreground mt-1">F1 Score</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                  <div className="text-3xl font-black text-yellow-400">0.35</div>
                  <div className="text-sm text-muted-foreground mt-1">Log Loss</div>
                </div>
              </div>
            </div>

            {/* Feature Importance */}
            <div className="rounded-xl border border-border bg-card p-6">
              <div className="flex items-center gap-2 mb-6">
                <Zap className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Top Features</h2>
              </div>
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
                ].map((feature) => (
                  <div key={feature.name} className="flex items-center gap-4">
                    <span className="w-48 text-sm text-muted-foreground truncate">
                      {feature.name}
                    </span>
                    <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                        style={{ width: `${feature.importance * 100 * 4}%` }}
                      />
                    </div>
                    <span className="w-12 text-sm text-right">
                      {(feature.importance * 100).toFixed(0)}%
                    </span>
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
