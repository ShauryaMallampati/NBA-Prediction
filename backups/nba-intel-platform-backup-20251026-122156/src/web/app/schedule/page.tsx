"use client"

import { useState } from "react"
import useSWR from "swr"
import { format } from "date-fns"

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface Prediction {
  game_id: string
  date: string
  home_team: string
  away_team: string
  home_win_prob: number
  away_win_prob: number
}

export default function SchedulePage() {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"))

  const {
    data: predictions,
    error,
    isLoading,
  } = useSWR<Prediction[]>(`http://localhost:8000/predictions?date=${selectedDate}`, fetcher)

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-muted/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">📅 Game Schedule</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 rounded-lg border border-border bg-muted text-foreground"
          />
        </div>

        {isLoading && <p className="text-muted-foreground">Loading predictions...</p>}

        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            Error loading predictions. Make sure the API is running (make serve).
          </div>
        )}

        {predictions && predictions.length === 0 && (
          <p className="text-muted-foreground">No games scheduled for this date.</p>
        )}

        <div className="space-y-4">
          {predictions?.map((pred) => (
            <div
              key={pred.game_id}
              className="p-6 rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-2">
                    <span className="text-lg font-semibold">{pred.away_team}</span>
                    <span className="text-muted-foreground">@</span>
                    <span className="text-lg font-semibold">{pred.home_team}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{pred.date}</p>
                </div>

                <div className="text-right">
                  <div className="text-3xl font-bold text-primary">{(pred.home_win_prob * 100).toFixed(1)}%</div>
                  <p className="text-sm text-muted-foreground">Home Win Prob</p>
                </div>
              </div>

              <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all" style={{ width: `${pred.home_win_prob * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
