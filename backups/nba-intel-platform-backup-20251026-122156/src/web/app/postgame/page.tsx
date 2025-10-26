export default function PostgamePage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-muted/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">📈 Postgame Analysis</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-6 rounded-lg border border-border bg-muted/30">
            <h2 className="text-xl font-semibold mb-4">Model Performance</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted-foreground">Accuracy</span>
                  <span className="font-bold">67.3%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-accent" style={{ width: "67.3%" }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted-foreground">Log Loss</span>
                  <span className="font-bold">0.542</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "45.8%" }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted-foreground">Brier Score</span>
                  <span className="font-bold">0.198</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-secondary" style={{ width: "80.2%" }} />
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-lg border border-border bg-muted/30">
            <h2 className="text-xl font-semibold mb-4">Calibration</h2>
            <p className="text-muted-foreground mb-4">
              Expected Calibration Error (ECE): <span className="font-bold text-foreground">0.032</span>
            </p>
            <div className="h-48 flex items-end justify-around gap-2">
              {[0.65, 0.82, 0.91, 0.88, 0.95, 0.89, 0.92, 0.96, 0.94, 0.98].map((height, i) => (
                <div key={i} className="flex-1 bg-primary/30 rounded-t" style={{ height: `${height * 100}%` }} />
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2 text-center">Calibration bins (predicted vs actual)</p>
          </div>

          <div className="md:col-span-2 p-6 rounded-lg border border-border bg-muted/30">
            <h2 className="text-xl font-semibold mb-4">Feature Importance (SHAP)</h2>
            <div className="space-y-3">
              {[
                { name: "Home advantage", value: 0.15 },
                { name: "Recent form (5 games)", value: 0.12 },
                { name: "Rest differential", value: 0.08 },
                { name: "Lineup chemistry", value: 0.06 },
                { name: "Social sentiment", value: 0.04 },
              ].map((feature) => (
                <div key={feature.name}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span>{feature.name}</span>
                    <span className="font-medium">{feature.value.toFixed(3)}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-secondary"
                      style={{ width: `${feature.value * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
