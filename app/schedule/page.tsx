'use client'

import { useState } from 'react'
import { useSchedule } from '@/lib/hooks'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { ErrorState } from '@/components/shared/error-state'
import { EmptyState } from '@/components/shared/empty-state'
import { formatShortDate, formatTime } from '@/lib/utils/format'
import { Calendar, ChevronLeft, ChevronRight, Clock } from 'lucide-react'

export default function SchedulePage() {
  const { data, isLoading, error, refetch } = useSchedule(14)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const games = data?.games || []

  // Group games by date
  const gamesByDate = games.reduce((acc, game) => {
    const dateStr = game.game_time || game.date
    const date = new Date(dateStr).toLocaleDateString('en-CA')
    if (!acc[date]) acc[date] = []
    acc[date].push(game)
    return acc
  }, {} as Record<string, typeof games>)

  const dates = Object.keys(gamesByDate).sort()
  const today = new Date().toLocaleDateString('en-CA')
  const displayDate = selectedDate || today
  const displayGames = gamesByDate[displayDate] || []

  const currentIndex = dates.indexOf(displayDate)
  const canGoBack = currentIndex > 0
  const canGoForward = currentIndex < dates.length - 1

  return (
    <div className="min-h-screen">
      {/* Page Header */}
      <header className="border-b border-border">
        <div className="container-wide py-8">
          <h1 className="text-2xl font-bold tracking-tight">Schedule</h1>
          <p className="text-muted-foreground">Upcoming NBA games over the next 14 days</p>
        </div>
      </header>

      <div className="container-wide py-8">
        {isLoading && <PageSkeleton />}

        {error && (
          <ErrorState message={error.message} retry={() => refetch()} />
        )}

        {data && !isLoading && (
          <>
            {/* Date Navigation */}
            <div className="flex items-center justify-between mb-6 p-4 bento-item">
              <button
                onClick={() => canGoBack && setSelectedDate(dates[currentIndex - 1])}
                disabled={!canGoBack}
                className="p-2 rounded-md hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <span className="text-lg font-semibold">
                  {new Date(displayDate + 'T12:00:00').toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })}
                </span>
                {displayDate === today && (
                  <span className="badge badge-success">Today</span>
                )}
              </div>

              <button
                onClick={() => canGoForward && setSelectedDate(dates[currentIndex + 1])}
                disabled={!canGoForward}
                className="p-2 rounded-md hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            {/* Quick Date Pills */}
            <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
              {dates.slice(0, 10).map((date) => (
                <button
                  key={date}
                  onClick={() => setSelectedDate(date)}
                  className={`flex-shrink-0 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${date === displayDate
                      ? 'bg-foreground text-background'
                      : 'border border-border hover:bg-accent'
                    }`}
                >
                  {formatShortDate(date + 'T12:00:00')}
                  {date === today && ' •'}
                </button>
              ))}
            </div>

            {/* Games Count */}
            <div className="mb-4 text-sm text-muted-foreground">
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
                    className="bento-item card-interactive"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground font-mono">
                        <Clock className="h-4 w-4" />
                        {game.game_time || formatTime(game.date)}
                      </div>
                      <span className="badge">Scheduled</span>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 rounded-md bg-muted/30">
                        <div>
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Home</div>
                          <div className="font-semibold">{game.home_team}</div>
                        </div>
                      </div>
                      <div className="text-center text-muted-foreground text-xs">vs</div>
                      <div className="flex items-center justify-between p-3 rounded-md bg-muted/30">
                        <div>
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Away</div>
                          <div className="font-semibold">{game.away_team}</div>
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
