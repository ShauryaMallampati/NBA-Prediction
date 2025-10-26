"use client"

import { NavHeader } from "@/components/nav-header"
import { Card } from "@/components/ui/card"

export default function PostgamePage() {
  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">📈 Postgame Analysis</h1>
          <p className="text-muted-foreground text-lg">Model performance metrics and calibration analysis</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">Model Performance</h2>
            <div className="space-y-5">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-muted-foreground">Accuracy</span>
                  <span className="font-bold text-lg">67.3%</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "67.3%" }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-muted-foreground">Log Loss</span>
                  <span className="font-bold text-lg">0.542</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-accent" style={{ width: "45.8%" }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">Lower is better</p>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-muted-foreground">Brier Score</span>
                  <span className="font-bold text-lg">0.198</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-secondary" style={{ width: "80.2%" }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">Lower is better</p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Calibration</h2>
            <p className="text-muted-foreground mb-4">
              Expected Calibration Error (ECE): <span className="font-bold text-foreground text-lg">0.032</span>
            </p>
            <div className="h-56 flex items-end justify-around gap-1 bg-muted/30 rounded-lg p-4">
              {[0.65, 0.82, 0.91, 0.88, 0.95, 0.89, 0.92, 0.96, 0.94, 0.98].map((height, i) => (
                <div
                  key={i}
                  className="flex-1 bg-gradient-to-t from-primary to-accent rounded-t transition-all hover:opacity-80"
                  style={{ height: `${height * 100}%` }}
                />
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-3 text-center">
              Calibration bins showing predicted vs actual win rates
            </p>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">Feature Importance (SHAP Values)</h2>
          <div className="space-y-4">
            {[
              { name: "Home advantage", value: 0.15, description: "Historical home court advantage" },
              { name: "Recent form (5 games)", value: 0.12, description: "Team performance in last 5 games" },
              { name: "Rest differential", value: 0.08, description: "Days of rest between teams" },
              { name: "Lineup chemistry", value: 0.06, description: "GNN-based player synergy scores" },
              { name: "Social sentiment", value: 0.04, description: "Fan sentiment from social media" },
              { name: "Injury impact", value: 0.03, description: "Key player availability" },
            ].map((feature) => (
              <div key={feature.name} className="p-4 rounded-lg bg-muted/50">
                <div className="flex justify-between mb-2">
                  <div>
                    <span className="font-medium">{feature.name}</span>
                    <p className="text-xs text-muted-foreground mt-1">{feature.description}</p>
                  </div>
                  <span className="font-bold text-lg">{feature.value.toFixed(3)}</span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary via-accent to-secondary transition-all"
                    style={{ width: `${(feature.value / 0.15) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </main>
    </div>
  )
}
