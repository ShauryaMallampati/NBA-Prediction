"use client"

import {
    Activity,
    AlertTriangle,
    Award,
    BarChart3,
    Brain,
    Target,
    TrendingUp,
    Zap,
} from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

interface ModelMetrics {
  overall: {
    training_accuracy: number
    cv_accuracy: number
    auc: number
    calibration: number
  }
  by_model: {
    xgboost: { accuracy: number; auc: number }
    lightgbm: { accuracy: number; auc: number }
    catboost: { accuracy: number; auc: number }
  }
  feature_importance: Array<{
    feature: string
    importance: number
  }>
}

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('/api/analytics')
      const data = await response.json()
      
      if (data.success && data.metrics) {
        setMetrics(data.metrics)
      } else {
        setError(data.message || 'Failed to load analytics')
      }
    } catch (err) {
      console.error('Error fetching analytics:', err)
      setError('Failed to fetch analytics data')
    } finally {
      setLoading(false)
    }
  }

  const formatPercent = (value: number) => (value * 100).toFixed(1) + '%'
  const formatFeatureName = (name: string) => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <p className="text-xl font-semibold text-foreground mb-2">Error Loading Analytics</p>
          <p className="text-muted-foreground">{error || 'Unknown error occurred'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">
      {/* Header */}
      <header className="glass-strong sticky top-0 z-50 border-b">
        <div className="container mx-auto px-6 py-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow-lg group-hover:scale-110 transition-transform duration-300">
              🏀
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
                NBA Intel
              </h1>
              <p className="text-xs text-muted-foreground font-medium">Performance Analytics</p>
            </div>
          </Link>
          <Link
            href="/predictions"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-all duration-300 glow-lg shadow-xl"
          >
            <Target className="w-5 h-5" />
            Predictions
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <Target className="w-8 h-8 text-primary" />
              <TrendingUp className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Training Accuracy</p>
            <p className="text-4xl font-black" style={{ fontFamily: "var(--font-display)" }}>
              {formatPercent(metrics.overall.training_accuracy)}
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-chart-4" />
              <Award className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">CV Accuracy</p>
            <p className="text-4xl font-black text-chart-4" style={{ fontFamily: "var(--font-display)" }}>
              {formatPercent(metrics.overall.cv_accuracy)}
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-chart-2" />
              <Zap className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">AUC Score</p>
            <p className="text-4xl font-black text-chart-2" style={{ fontFamily: "var(--font-display)" }}>
              {formatPercent(metrics.overall.auc)}
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <Brain className="w-8 h-8 text-chart-5" />
              <TrendingUp className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Calibration</p>
            <p className="text-4xl font-black text-chart-5" style={{ fontFamily: "var(--font-display)" }}>
              {formatPercent(metrics.overall.calibration)}
            </p>
          </div>
        </div>

        {/* Model Comparison */}
        <div className="mb-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <Brain className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Ensemble Model Comparison</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* XGBoost */}
            <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20">
              <h3 className="text-lg font-bold mb-4 text-blue-400">XGBoost</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Accuracy</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-blue-500"
                        style={{ width: formatPercent(metrics.by_model.xgboost.accuracy) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.xgboost.accuracy)}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">AUC</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-blue-500"
                        style={{ width: formatPercent(metrics.by_model.xgboost.auc) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.xgboost.auc)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* LightGBM */}
            <div className="p-6 rounded-xl bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20">
              <h3 className="text-lg font-bold mb-4 text-green-400">LightGBM</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Accuracy</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-green-500"
                        style={{ width: formatPercent(metrics.by_model.lightgbm.accuracy) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.lightgbm.accuracy)}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">AUC</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-green-500"
                        style={{ width: formatPercent(metrics.by_model.lightgbm.auc) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.lightgbm.auc)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* CatBoost */}
            <div className="p-6 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20">
              <h3 className="text-lg font-bold mb-4 text-purple-400">CatBoost</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Accuracy</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-purple-500"
                        style={{ width: formatPercent(metrics.by_model.catboost.accuracy) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.catboost.accuracy)}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">AUC</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-purple-500"
                        style={{ width: formatPercent(metrics.by_model.catboost.auc) }}
                      />
                    </div>
                    <span className="text-sm font-bold">{formatPercent(metrics.by_model.catboost.auc)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Importance */}
        <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Top 10 Most Important Features</h2>
          </div>

          <div className="space-y-4">
            {metrics.feature_importance.map((feature, idx) => (
              <div key={feature.feature} className="flex items-center gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold">{formatFeatureName(feature.feature)}</span>
                    <span className="text-sm font-bold text-muted-foreground">{formatPercent(feature.importance)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-secondary"
                      style={{ width: formatPercent(feature.importance / metrics.feature_importance[0].importance) }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
