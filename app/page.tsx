import {
    Activity,
    ArrowRight,
    BarChart3,
    Brain,
    Calendar,
    MessageSquare,
    Target,
    TrendingUp,
    Users,
    Zap,
} from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">
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
              <p className="text-xs text-muted-foreground font-medium">ML-Powered Analytics</p>
            </div>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href="/predictions"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Predictions
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/betting"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Betting
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/analytics"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Analytics
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/schedule"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Schedule
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/live" className="text-sm font-semibold hover:text-primary transition-colors relative group">
              Live
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/chemistry"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Chemistry
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/sentiment"
              className="text-sm font-semibold hover:text-primary transition-colors relative group"
            >
              Sentiment
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary group-hover:w-full transition-all duration-300" />
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6">
        <div className="max-w-7xl mx-auto text-center py-24 md:py-32 space-y-10">
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full glass-strong border-2 border-primary/20 text-sm font-bold mb-6 animate-pulse-slow">
            <Brain className="w-5 h-5 text-primary" />
            <span>Powered by Advanced Machine Learning</span>
          </div>

          <h2
            className="text-7xl md:text-9xl font-black text-balance leading-[0.9] tracking-tighter"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Predict Every
            <br />
            <span className="text-gradient">NBA Game</span>
          </h2>

          <p className="text-xl md:text-3xl text-muted-foreground text-pretty max-w-4xl mx-auto leading-relaxed font-medium">
            Real-time predictions, live win probability, player chemistry networks, and social sentiment analysis—all
            powered by cutting-edge AI
          </p>

          <div className="flex flex-wrap items-center justify-center gap-6 pt-8">
            <Link
              href="/schedule"
              className="group inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-primary text-primary-foreground font-bold text-lg hover:scale-105 transition-all duration-300 glow-lg shadow-2xl"
            >
              View Schedule
              <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </Link>
            <Link
              href="/live"
              className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl glass-strong font-bold text-lg hover:bg-accent hover:scale-105 transition-all duration-300 border-2"
            >
              <Activity className="w-5 h-5" />
              Live Games
            </Link>
          </div>
        </div>

        <div className="max-w-7xl mx-auto grid md:grid-cols-6 gap-6 mb-24">
          <Link
            href="/schedule"
            className="group md:col-span-4 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/20"
          >
            <Calendar className="w-16 h-16 text-primary mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Game Schedule & Predictions
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-2xl">
              Pregame win probabilities powered by Elo ratings and LightGBM ensemble models with comprehensive feature
              engineering
            </p>
            <div className="flex items-center gap-3 text-primary font-bold text-lg">
              Explore Schedule
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/live"
            className="group md:col-span-2 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-secondary/50 hover:shadow-2xl hover:shadow-secondary/20"
          >
            <TrendingUp className="w-16 h-16 text-secondary mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-4xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Live Game Center
            </h3>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Real-time win probability tracking with possession-by-possession updates
            </p>
            <div className="flex items-center gap-3 text-secondary font-bold">
              Watch Live
              <ArrowRight className="w-5 h-5 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/chemistry"
            className="group md:col-span-2 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-3/50 hover:shadow-2xl hover:shadow-chart-3/20"
          >
            <Users className="w-16 h-16 text-chart-3 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-4xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Player Chemistry
            </h3>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              Graph Neural Network analysis of player synergies and lineup effectiveness
            </p>
            <div className="flex items-center gap-3 text-chart-3 font-bold">
              Analyze Chemistry
              <ArrowRight className="w-5 h-5 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/sentiment"
            className="group md:col-span-4 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-4/50 hover:shadow-2xl hover:shadow-chart-4/20"
          >
            <MessageSquare className="w-16 h-16 text-chart-4 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Social Sentiment Analysis
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-3xl">
              Track social media buzz and sentiment from Twitter, Reddit, and YouTube using transformer models
            </p>
            <div className="flex items-center gap-3 text-chart-4 font-bold text-lg">
              View Sentiment
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>

          <Link
            href="/postgame"
            className="group md:col-span-6 p-12 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-500 hover:scale-[1.02] border-2 hover:border-chart-5/50 hover:shadow-2xl hover:shadow-chart-5/20"
          >
            <BarChart3 className="w-16 h-16 text-chart-5 mb-8 group-hover:scale-110 transition-transform glow" />
            <h3 className="text-5xl font-black mb-6 text-balance" style={{ fontFamily: "var(--font-display)" }}>
              Postgame Analysis & Model Performance
            </h3>
            <p className="text-xl text-muted-foreground leading-relaxed mb-8 max-w-4xl">
              Comprehensive model evaluation with calibration curves, SHAP explanations, and performance metrics
            </p>
            <div className="flex items-center gap-3 text-chart-5 font-bold text-lg">
              View Analytics
              <ArrowRight className="w-6 h-6 group-hover:translate-x-3 transition-transform" />
            </div>
          </Link>
        </div>

        <div className="max-w-7xl mx-auto mb-32">
          <div className="text-center mb-20">
            <h3 className="text-6xl font-black mb-6" style={{ fontFamily: "var(--font-display)" }}>
              Platform Capabilities
            </h3>
            <p className="text-2xl text-muted-foreground font-medium">
              Advanced ML models and real-time data processing
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Target,
                title: "Pregame Predictions",
                desc: "Elo + LightGBM ensemble with 70%+ accuracy",
                color: "text-primary",
              },
              {
                icon: Activity,
                title: "Live Win Probability",
                desc: "GRU sequences for possession-level updates",
                color: "text-secondary",
              },
              {
                icon: Zap,
                title: "Video Analysis",
                desc: "ResNet3D for highlight and foul detection",
                color: "text-chart-3",
              },
              {
                icon: Users,
                title: "Player Chemistry",
                desc: "Graph Neural Networks for lineup synergy",
                color: "text-chart-4",
              },
              {
                icon: MessageSquare,
                title: "Social Sentiment",
                desc: "DistilBERT transformers for text analysis",
                color: "text-chart-5",
              },
              {
                icon: Brain,
                title: "Model Explainability",
                desc: "SHAP values for prediction interpretation",
                color: "text-primary",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group p-10 rounded-3xl glass-strong hover:bg-accent/50 transition-all duration-300 hover:scale-105 border-2 hover:border-primary/30 hover:shadow-xl"
              >
                <feature.icon
                  className={`w-14 h-14 ${feature.color} mb-6 group-hover:scale-110 transition-transform glow`}
                />
                <h4 className="text-2xl font-bold mb-3" style={{ fontFamily: "var(--font-display)" }}>
                  {feature.title}
                </h4>
                <p className="text-muted-foreground leading-relaxed text-lg">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t glass-strong mt-32">
        <div className="container mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow">
                🏀
              </div>
              <div>
                <p className="font-black text-lg" style={{ fontFamily: "var(--font-display)" }}>
                  NBA Intelligence Platform
                </p>
                <p className="text-sm text-muted-foreground font-medium">Research Use Only • v0.1.0</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground font-medium">Powered by Next.js, FastAPI, PyTorch & LightGBM</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
