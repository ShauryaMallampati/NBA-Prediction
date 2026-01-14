'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { useSchedule } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { formatShortDate, formatTime } from '@/lib/utils/format'
import { Calendar, ChevronLeft, ChevronRight, Clock } from 'lucide-react'

export default function SchedulePage() {
  // Use schedule endpoint for 14-day view (better for future planning)
  const { data, isLoading, error, refetch } = useSchedule(14)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const games = data?.games || []

  // Group games by date (using local date to match "today")
  const gamesByDate = games.reduce((acc, game) => {
    // Convert UTC game time to local YYYY-MM-DD
    // If game.date is already YYYY-MM-DD, new Date() parses it as UTC midnight,
    // so toLocaleDateString might shift it back a day depending on browser timezone!
    // Wait, if it comes from predictions it was ISO. 
    // From live_schedule, it's YYYY-MM-DD (split T).
    // Actually, live_schedule also provides `game_time` (ISO). 
    // We should use `game.game_time` if available for accurate local conversion.

    const dateStr = game.game_time || game.date
    const date = new Date(dateStr).toLocaleDateString('en-CA')

    if (!acc[date]) acc[date] = []
    acc[date].push(game)
    return acc
  }, {} as Record<string, typeof games>)

  const dates = Object.keys(gamesByDate).sort()
  // Use local date for "today" to avoid UTC shifting
  const today = new Date().toLocaleDateString('en-CA')
  const displayDate = selectedDate || today

  const displayGames = gamesByDate[displayDate] || []

  const currentIndex = dates.indexOf(displayDate)
  const canGoBack = currentIndex > 0
  const canGoForward = currentIndex < dates.length - 1

  return (
    <div className="min-h-screen">
      <Header
        title="Schedule"
        description="Upcoming NBA games"
      />

      <div className="container mx-auto px-6 py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState
            message={error.message}
            retry={() => refetch()}
          />
        )}

        {data && !isLoading && (
          <>
            {/* Date Navigation */}
            <div className="flex items-center justify-between mb-8 p-4 rounded-xl border border-border bg-card">
              <button
                onClick={() => canGoBack && setSelectedDate(dates[currentIndex - 1])}
                disabled={!canGoBack}
                className="p-2 rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-primary" />
                <span className="text-lg font-bold">
                  {new Date(displayDate + 'T12:00:00').toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })}
                </span>
                {displayDate === today && (
                  <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-primary/10 text-primary">
                    Today
                  </span>
                )}
              </div>

              <button
                onClick={() => canGoForward && setSelectedDate(dates[currentIndex + 1])}
                disabled={!canGoForward}
                className="p-2 rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            {/* Quick Date Pills */}
            <div className="flex gap-2 overflow-x-auto pb-4 mb-6 scrollbar-hide">
              {dates.slice(0, 10).map((date) => (
                <button
                  key={date}
                  onClick={() => setSelectedDate(date)}
                  className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${date === displayDate
                    ? 'bg-primary text-primary-foreground'
                    : 'border border-border hover:bg-accent'
                    }`}
                >
                  {formatShortDate(date + 'T12:00:00')}
                  {date === today && ' (Today)'}
                </button>
              ))}
            </div>

            {/* Games Count */}
            <div className="mb-6 text-sm text-muted-foreground">
              {displayGames.length} game{displayGames.length !== 1 ? 's' : ''} scheduled
            </div>

            {/* Games Grid */}
            {displayGames.length === 0 ? (
              <EmptyState
                title="No Games Scheduled"
                description="There are no games scheduled for this date."
                icon="calendar"
              />
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {displayGames.map((game) => (
                  <div
                    key={game.game_id}
                    className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-all"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        {game.game_time || formatTime(game.date)}
                      </div>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                        Scheduled
                      </span>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                        <div>
                          <div className="text-xs text-muted-foreground">HOME</div>
                          <div className="font-bold">{game.home_team}</div>
                        </div>
                      </div>
                      <div className="text-center text-muted-foreground text-sm">vs</div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                        <div>
                          <div className="text-xs text-muted-foreground">AWAY</div>
                          <div className="font-bold">{game.away_team}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
