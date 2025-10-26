"use client"

import { NavHeader } from "@/components/nav-header"
import { Card } from "@/components/ui/card"

export default function ChemistryPage() {
  const chemistryData = [
    { player1: "LeBron James", player2: "Anthony Davis", score: 0.92, games: 156 },
    { player1: "Stephen Curry", player2: "Klay Thompson", score: 0.89, games: 412 },
    { player1: "Nikola Jokic", player2: "Jamal Murray", score: 0.87, games: 203 },
    { player1: "Luka Doncic", player2: "Kyrie Irving", score: 0.85, games: 78 },
    { player1: "Joel Embiid", player2: "Tyrese Maxey", score: 0.83, games: 124 },
  ]

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🧪 Player Chemistry Analysis</h1>
          <p className="text-muted-foreground text-lg">
            Graph Neural Network analysis of player synergies and on-court chemistry
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">How Chemistry is Calculated</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>
                <span className="font-medium text-foreground">Graph Neural Networks (GNN)</span> analyze player
                interactions by treating players as nodes and their on-court relationships as edges.
              </p>
              <p>
                The model considers: shared court time, assist connections, defensive rotations, spacing patterns, and
                win/loss outcomes when paired together.
              </p>
              <p>
                Chemistry scores range from 0-1, where higher scores indicate stronger positive synergy between players.
              </p>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Impact on Predictions</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">High chemistry lineups</span>
                <span className="font-bold text-primary">+5-8% win probability</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">New player pairings</span>
                <span className="font-bold text-muted-foreground">Neutral impact</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Poor chemistry lineups</span>
                <span className="font-bold text-destructive">-3-6% win probability</span>
              </div>
            </div>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Top Player Duos</h2>
          <div className="space-y-4">
            {chemistryData.map((duo, index) => (
              <div key={index} className="p-4 rounded-lg bg-muted/50 border border-border">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl font-bold text-muted-foreground">#{index + 1}</span>
                      <span className="text-lg font-semibold">
                        {duo.player1} + {duo.player2}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{duo.games} games played together</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-primary">{(duo.score * 100).toFixed(0)}</div>
                    <p className="text-sm text-muted-foreground">Chemistry Score</p>
                  </div>
                </div>

                <div className="h-2 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all"
                    style={{ width: `${duo.score * 100}%` }}
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
