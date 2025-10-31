"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  TrendingUp,
  Target,
  DollarSign,
  Activity,
  BarChart3,
  LineChart,
  PieChart,
  Calendar,
  Award,
  AlertTriangle,
} from "lucide-react"

interface ModelMetrics {
  stat: string
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  roc_auc: number
  calibration_score: number
}

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([])
  const [loading, setLoading] = useState(true)

  // Mock data for now - will be replaced with real API calls
  useEffect(() => {
    const mockMetrics: ModelMetrics[] = [
      { stat: "PTS", accuracy: 0.712, precision: 0.698, recall: 0.745, f1_score: 0.721, roc_auc: 0.782, calibration_score: 0.891 },
      { stat: "AST", accuracy: 0.689, precision: 0.671, recall: 0.712, f1_score: 0.691, roc_auc: 0.756, calibration_score: 0.867 },
      { stat: "REB", accuracy: 0.701, precision: 0.688, recall: 0.723, f1_score: 0.705, roc_auc: 0.769, calibration_score: 0.879 },
      { stat: "STL", accuracy: 0.678, precision: 0.662, recall: 0.698, f1_score: 0.679, roc_auc: 0.741, calibration_score: 0.854 },
      { stat: "BLK", accuracy: 0.685, precision: 0.669, recall: 0.705, f1_score: 0.686, roc_auc: 0.748, calibration_score: 0.861 },
    ]
    
    setMetrics(mockMetrics)
    setLoading(false)
  }, [])

  const avgAccuracy = metrics.length > 0 
    ? (metrics.reduce((sum, m) => sum + m.accuracy, 0) / metrics.length * 100).toFixed(1)
    : "0.0"

  const avgCalibration = metrics.length > 0
    ? (metrics.reduce((sum, m) => sum + m.calibration_score, 0) / metrics.length * 100).toFixed(1)
    : "0.0"

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
            <p className="text-sm text-muted-foreground font-semibold mb-1">Avg Accuracy</p>
            <p className="text-4xl font-black" style={{ fontFamily: "var(--font-display)" }}>
              {avgAccuracy}%
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-chart-4" />
              <Award className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Calibration</p>
            <p className="text-4xl font-black text-chart-4" style={{ fontFamily: "var(--font-display)" }}>
              {avgCalibration}%
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-chart-2" />
              <CheckCircle2 className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">Total Predictions</p>
            <p className="text-4xl font-black text-chart-2" style={{ fontFamily: "var(--font-display)" }}>
              2.4K
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-strong border-2 border-primary/10 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="w-8 h-8 text-chart-5" />
              <TrendingUp className="w-5 h-5 text-chart-5" />
            </div>
            <p className="text-sm text-muted-foreground font-semibold mb-1">ROI (Simulated)</p>
            <p className="text-4xl font-black text-chart-5" style={{ fontFamily: "var(--font-display)" }}>
              +12.3%
            </p>
          </div>
        </div>

        {/* Model Performance Table */}
        <div className="mb-12 p-8 rounded-3xl glass-strong border-2 border-primary/10">
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">Model Performance by Stat</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-4 px-4 text-sm font-bold text-muted-foreground">Stat</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">Accuracy</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">Precision</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">Recall</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">F1 Score</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">ROC AUC</th>
                  <th className="text-right py-4 px-4 text-sm font-bold text-muted-foreground">Calibration</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric) => (
                  <tr key={metric.stat} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
                    <td className="py-4 px-4">
                      <span className="font-bold text-lg">{metric.stat}</span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-2 rounded-full bg-muted overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-primary to-chart-5"
                            style={{ width: `${metric.accuracy * 100}%` }}
                          />
                        </div>
                        <span className="font-bold w-12">{(metric.accuracy * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right font-bold">{(metric.precision * 100).toFixed(1)}%</td>
                    <td className="py-4 px-4 text-right font-bold">{(metric.recall * 100).toFixed(1)}%</td>
                    <td className="py-4 px-4 text-right font-bold">{(metric.f1_score * 100).toFixed(1)}%</td>
                    <td className="py-4 px-4 text-right font-bold text-primary">{(metric.roc_auc * 100).toFixed(1)}%</td>
                    <td className="py-4 px-4 text-right">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-chart-5/20 text-chart-5 font-bold">
                        <Award className="w-4 h-4" />
                        {(metric.calibration_score * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Feature Importance & Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Features */}
          <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10">
            <div className="flex items-center gap-3 mb-6">
              <LineChart className="w-6 h-6 text-primary" />
              <h3 className="text-xl font-bold">Top Features</h3>
            </div>
            
            <div className="space-y-4">
              {[
                { name: "Recent Performance (L5)", importance: 0.18 },
                { name: "Matchup History", importance: 0.15 },
                { name: "Home/Away", importance: 0.12 },
                { name: "Minutes per Game", importance: 0.11 },
                { name: "Team Pace", importance: 0.09 },
                { name: "Rest Days", importance: 0.08 },
                { name: "Usage Rate", importance: 0.07 },
                { name: "Opponent Defense", importance: 0.06 },
              ].map((feature, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-muted-foreground w-48">{feature.name}</span>
                  <div className="flex-1 h-6 rounded-full bg-muted overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-chart-5 flex items-center justify-end px-2"
                      style={{ width: `${feature.importance * 100}%` }}
                    >
                      <span className="text-xs font-bold text-white">{(feature.importance * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Insights */}
          <div className="p-8 rounded-3xl glass-strong border-2 border-primary/10">
            <div className="flex items-center gap-3 mb-6">
              <PieChart className="w-6 h-6 text-primary" />
              <h3 className="text-xl font-bold">Recent Insights</h3>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-chart-5/10 border-2 border-chart-5/20">
                <div className="flex items-start gap-3">
                  <Award className="w-5 h-5 text-chart-5 flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-bold text-chart-5 mb-1">High Confidence Week</p>
                    <p className="text-sm text-muted-foreground">
                      Last 7 days showed 8.2% improvement in calibration scores across all models.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-chart-2/10 border-2 border-chart-2/20">
                <div className="flex items-start gap-3">
                  <Activity className="w-5 h-5 text-chart-2 flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-bold text-chart-2 mb-1">PTS Model Leading</p>
                    <p className="text-sm text-muted-foreground">
                      Points predictions maintaining 71.2% accuracy with excellent calibration.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-chart-4/10 border-2 border-chart-4/20">
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-chart-4 flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-bold text-chart-4 mb-1">2,431 Predictions Made</p>
                    <p className="text-sm text-muted-foreground">
                      Successfully processed predictions for 487 unique players this season.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-destructive/10 border-2 border-destructive/20">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-bold text-destructive mb-1">Monitor STL Model</p>
                    <p className="text-sm text-muted-foreground">
                      Steals predictions showing slight variance - may need recalibration.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function CheckCircle2(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}
