"use client"

import { NavHeader } from "@/components/nav-header"
import { Card } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const sentimentTrend = [
  { date: "Jan 1", sentiment: 0.65 },
  { date: "Jan 8", sentiment: 0.72 },
  { date: "Jan 15", sentiment: 0.68 },
  { date: "Jan 22", sentiment: 0.75 },
  { date: "Jan 29", sentiment: 0.71 },
  { date: "Feb 5", sentiment: 0.78 },
  { date: "Feb 12", sentiment: 0.82 },
]

export default function SentimentPage() {
  const teamSentiment = [
    { team: "Lakers", sentiment: 0.82, change: "+12%", posts: 45230 },
    { team: "Warriors", sentiment: 0.78, change: "+8%", posts: 38920 },
    { team: "Celtics", sentiment: 0.75, change: "-3%", posts: 42100 },
    { team: "Nuggets", sentiment: 0.73, change: "+5%", posts: 31450 },
    { team: "76ers", sentiment: 0.68, change: "-8%", posts: 28760 },
  ]

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">💬 Social Sentiment Analysis</h1>
          <p className="text-muted-foreground text-lg">
            Real-time sentiment tracking from Twitter, Reddit, and YouTube using transformer models
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Data Sources</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Twitter/X</span>
                <span className="text-sm font-bold">~50K posts/day</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Reddit</span>
                <span className="text-sm font-bold">~15K posts/day</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">YouTube</span>
                <span className="text-sm font-bold">~5K comments/day</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Model</h3>
            <p className="text-sm mb-3">DistilBERT fine-tuned on sports sentiment</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Accuracy</span>
                <span className="font-bold">87.3%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">F1 Score</span>
                <span className="font-bold">0.854</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Impact</h3>
            <p className="text-sm text-muted-foreground">
              Sentiment contributes <span className="font-bold text-foreground">2-4%</span> to win probability
              predictions, especially for home games with strong fan support.
            </p>
          </Card>
        </div>

        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Sentiment Trend (Last 7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sentimentTrend}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="date" className="text-muted-foreground" />
              <YAxis
                className="text-muted-foreground"
                domain={[0, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
              />
              <Line type="monotone" dataKey="sentiment" stroke="hsl(var(--primary))" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">Team Sentiment Rankings</h2>
          <div className="space-y-4">
            {teamSentiment.map((team, index) => (
              <div key={index} className="p-4 rounded-lg bg-muted/50 border border-border">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-xl font-bold text-muted-foreground">#{index + 1}</span>
                      <span className="text-lg font-semibold">{team.team}</span>
                      <span
                        className={`text-sm font-medium ${
                          team.change.startsWith("+") ? "text-primary" : "text-destructive"
                        }`}
                      >
                        {team.change}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{team.posts.toLocaleString()} social posts analyzed</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-primary">{(team.sentiment * 100).toFixed(0)}</div>
                    <p className="text-sm text-muted-foreground">Sentiment</p>
                  </div>
                </div>

                <div className="h-2 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all"
                    style={{ width: `${team.sentiment * 100}%` }}
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
