"use client"

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
    <div className="min-h-screen">
      <header className="border-b border-border bg-muted/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">📊 Live Game Center</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="p-6 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold">Lakers vs Warriors</h2>
                  <p className="text-muted-foreground">Q3 • 5:23 remaining</p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold">98 - 94</div>
                </div>
              </div>

              <div className="mb-2 flex justify-between text-sm">
                <span>Lakers Win Probability</span>
                <span className="font-bold text-primary">68%</span>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: "68%" }} />
              </div>
            </div>

            <div className="p-6 rounded-lg border border-border bg-muted/30">
              <h3 className="text-lg font-semibold mb-4">Win Probability Chart</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis
                    dataKey="possession"
                    stroke="#71717a"
                    label={{ value: "Possession", position: "insideBottom", offset: -5 }}
                  />
                  <YAxis stroke="#71717a" domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46" }}
                    formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
                  />
                  <Line type="monotone" dataKey="homeWinProb" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-lg border border-border bg-muted/30">
              <h3 className="text-lg font-semibold mb-4">Play-by-Play</h3>
              <div className="space-y-3 text-sm">
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">5:23 Q3</p>
                  <p className="text-muted-foreground">LeBron James makes 3-pt shot</p>
                </div>
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">5:45 Q3</p>
                  <p className="text-muted-foreground">Stephen Curry misses jumper</p>
                </div>
                <div className="pb-3 border-b border-border">
                  <p className="font-medium">6:12 Q3</p>
                  <p className="text-muted-foreground">Anthony Davis defensive rebound</p>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-lg border border-border bg-muted/30">
              <h3 className="text-lg font-semibold mb-4">Key Factors</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Recent momentum</span>
                  <span className="font-medium">+12%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Foul trouble</span>
                  <span className="font-medium">-3%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Lineup strength</span>
                  <span className="font-medium">+8%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
