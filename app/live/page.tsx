"use client"

import { NavHeader } from "@/components/nav-header"
import { Card } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

// Mock data for demonstration
const mockData = [
  { possession: 0, homeWinProb: 0.52 },
  { possession: 10, homeWinProb: 0.55 },
  { possession: 20, homeWinProb: 0.58 },
  { possession: 30, homeWinProb: 0.62 },
  { possession: 40, homeWinProb: 0.59 },
  { possession: 50, homeWinProb: 0.65 },
  { possession: 60, homeWinProb: 0.68 },
]

export default function LivePage() {
  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">📊 Live Game Center</h1>
          <p className="text-muted-foreground text-lg">Real-time win probability powered by GRU sequences</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold">Lakers vs Warriors</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-muted-foreground">Q3 • 5:23 remaining</p>
                    <span className="px-2 py-1 text-xs font-medium bg-destructive/20 text-destructive rounded-full animate-pulse">
                      LIVE
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold">98 - 94</div>
                </div>
              </div>

              <div className="mb-2 flex justify-between text-sm">
                <span>Lakers Win Probability</span>
                <span className="font-bold text-primary text-lg">68%</span>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all duration-500" style={{ width: "68%" }} />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-4">Win Probability Chart</h3>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={mockData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis
                    dataKey="possession"
                    className="text-muted-foreground"
                    label={{ value: "Possession", position: "insideBottom", offset: -5 }}
                  />
                  <YAxis
                    className="text-muted-foreground"
                    domain={[0, 1]}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                    formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, "Win Probability"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="homeWinProb"
                    stroke="hsl(var(--primary))"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Play-by-Play</h3>
              <div className="space-y-3 text-sm max-h-96 overflow-y-auto">
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">5:23 Q3</p>
                  <p className="text-muted-foreground">LeBron James makes 3-pt shot</p>
                  <p className="text-xs text-primary mt-1">Win prob: 68% (+3%)</p>
                </div>
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">5:45 Q3</p>
                  <p className="text-muted-foreground">Stephen Curry misses jumper</p>
                  <p className="text-xs text-muted-foreground mt-1">Win prob: 65%</p>
                </div>
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">6:12 Q3</p>
                  <p className="text-muted-foreground">Anthony Davis defensive rebound</p>
                  <p className="text-xs text-muted-foreground mt-1">Win prob: 65%</p>
                </div>
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">6:34 Q3</p>
                  <p className="text-muted-foreground">Klay Thompson makes 2-pt shot</p>
                  <p className="text-xs text-destructive mt-1">Win prob: 62% (-3%)</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Key Factors (SHAP)</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Recent momentum</span>
                  <span className="font-medium text-primary">+12%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Foul trouble</span>
                  <span className="font-medium text-destructive">-3%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Lineup strength</span>
                  <span className="font-medium text-primary">+8%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Time remaining</span>
                  <span className="font-medium">+5%</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
