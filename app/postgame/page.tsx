'use client'

import { useEffect, useState } from 'react'
import { BarChart3, Gauge, Sparkles } from 'lucide-react'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'

interface AnalyticsResponse {
  success: boolean
  metrics: {
    overall: {
      training_accuracy: number | null
      cv_accuracy: number | null
      auc: number | null
      calibration: number | null
    }
    by_model: Record<string, { accuracy: number | null; auc: number | null }>
    feature_importance: Array<{ feature: string; importance: number }>
  }
  generated_at: string
}

export default function PostgamePage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch('/api/analytics')
        if (!response.ok) throw new Error('Failed to load analytics')
        const json = (await response.json()) as AnalyticsResponse
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    loadAnalytics()
  }, [])

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <div className="flex items-center gap-3 mb-2">
            <Gauge className="h-6 w-6 text-muted-foreground" />
            <h1 className="text-2xl font-bold tracking-tight">Postgame Performance</h1>
          </div>
          <p className="text-muted-foreground">Calibration, accuracy, and feature impact from the latest model run.</p>
        </div>
      </header>

      <div className="container-wide py-8">
        {loading && <PageSkeleton />}
        {error && <ErrorState message={error} retry={() => window.location.reload()} />}

        {!loading && !error && data && (
          <div className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="bento-item">
                <h2 className="text-lg font-semibold mb-4">Overall Performance</h2>
                <MetricBar label="Training Accuracy" value={data.metrics.overall.training_accuracy} />
                <MetricBar label="Cross-Validation" value={data.metrics.overall.cv_accuracy} />
                <MetricBar label="AUC" value={data.metrics.overall.auc} />
                <MetricBar label="Calibration" value={data.metrics.overall.calibration} />
                <div className="mt-4 text-xs text-muted-foreground">
                  Generated {new Date(data.generated_at).toLocaleString()}
                </div>
              </div>

              <div className="bento-item">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="h-4 w-4 text-muted-foreground" />
                  <h2 className="text-lg font-semibold">Model Breakdown</h2>
                </div>
                <div className="space-y-4">
                  {Object.entries(data.metrics.by_model).map(([model, metrics]) => (
                    <div key={model} className="p-3 rounded-md bg-muted/40 border border-border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium capitalize">{model}</span>
                      <span className="text-xs text-muted-foreground">
                        AUC {typeof metrics.auc === 'number' ? metrics.auc.toFixed(2) : '—'}
                      </span>
                      </div>
                      <div className="prob-bar">
                        <div
                          className="prob-bar-fill bg-foreground"
                          style={{ width: `${typeof metrics.accuracy === 'number' ? metrics.accuracy * 100 : 0}%` }}
                        />
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        Accuracy {typeof metrics.accuracy === 'number' ? `${(metrics.accuracy * 100).toFixed(1)}%` : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bento-item">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-lg font-semibold">Top Feature Importance</h2>
              </div>
              <div className="space-y-3">
                {data.metrics.feature_importance.slice(0, 8).map((feature) => (
                  <div key={feature.feature} className="flex items-center gap-4">
                    <div className="w-48 text-sm text-muted-foreground truncate">{feature.feature}</div>
                    <div className="flex-1">
                      <div className="prob-bar">
                        <div
                          className="prob-bar-fill bg-foreground"
                          style={{ width: `${feature.importance * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-12 text-right text-sm font-mono">
                      {(feature.importance * 100).toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MetricBar({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between text-sm text-muted-foreground mb-1">
        <span>{label}</span>
        <span className="font-mono text-foreground">
          {typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—'}
        </span>
      </div>
      <div className="prob-bar">
        <div
          className="prob-bar-fill bg-foreground"
          style={{ width: `${typeof value === 'number' ? value * 100 : 0}%` }}
        />
      </div>
    </div>
  )
}
