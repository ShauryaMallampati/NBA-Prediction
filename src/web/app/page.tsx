import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border bg-muted/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-primary">🏀 NBA Intelligence Platform</h1>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4">
            <h2 className="text-5xl font-bold text-balance">ML-Powered NBA Predictions</h2>
            <p className="text-xl text-muted-foreground text-pretty">
              Pregame predictions, live win probability, player chemistry analysis, and social sentiment insights—all
              powered by real data and advanced ML.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <Link
              href="/schedule"
              className="p-6 rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="text-4xl mb-4">📅</div>
              <h3 className="text-xl font-semibold mb-2">Schedule</h3>
              <p className="text-muted-foreground">View upcoming games with pregame win probabilities</p>
            </Link>

            <Link
              href="/live"
              className="p-6 rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">Game Center</h3>
              <p className="text-muted-foreground">Live win probability and possession-by-possession updates</p>
            </Link>

            <Link
              href="/postgame"
              className="p-6 rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="text-4xl mb-4">📈</div>
              <h3 className="text-xl font-semibold mb-2">Postgame</h3>
              <p className="text-muted-foreground">Model performance, calibration curves, and insights</p>
            </Link>
          </div>

          <div className="mt-16 p-8 rounded-lg bg-primary/10 border border-primary/20">
            <h3 className="text-2xl font-bold mb-4">Features</h3>
            <ul className="grid md:grid-cols-2 gap-4 text-left">
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>Pregame predictions with Elo + LightGBM</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>Live win probability (GRU sequences)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>Video highlight detection</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>Player chemistry via GNN</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>Social sentiment analysis</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">✓</span>
                <span>SHAP explanations</span>
              </li>
            </ul>
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>NBA Intelligence Platform v0.1.0 • Research Use Only</p>
        </div>
      </footer>
    </div>
  )
}
