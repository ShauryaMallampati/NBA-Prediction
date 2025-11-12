"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowLeft, Calendar, ChevronLeft, ChevronRight, RefreshCw, Clock, MapPin } from "lucide-react"

interface Game {
  game_id: string
  date: string
  home_team: string
  away_team: string
  game_time: string
  season: string
}

interface GamesByDate {
  [date: string]: Game[]
}

export default function SchedulePage() {
  const [gamesByDate, setGamesByDate] = useState<GamesByDate>({})
  const [dates, setDates] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [currentMonth, setCurrentMonth] = useState<string>(new Date().toISOString().slice(0, 7))
  
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]

  useEffect(() => {
    fetchSchedule()
  }, [currentMonth])

  const fetchSchedule = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/schedule?month=${currentMonth}`)
      const data = await response.json()
      
      if (data.error) {
        console.error('Error fetching schedule:', data.error)
        return
      }

      setGamesByDate(data.games_by_date || {})
      setDates(data.dates || [])
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const changeMonth = (direction: 'prev' | 'next') => {
    const [year, month] = currentMonth.split('-').map(Number)
    let newYear = year
    let newMonth = month

    if (direction === 'prev') {
      newMonth -= 1
      if (newMonth < 1) {
        newMonth = 12
        newYear -= 1
      }
    } else {
      newMonth += 1
      if (newMonth > 12) {
        newMonth = 1
        newYear += 1
      }
    }

    setCurrentMonth(`${newYear}-${String(newMonth).padStart(2, '0')}`)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  const isToday = (dateStr: string) => {
    const today = new Date()
    today.setHours(today.getHours() - 8)
    const todayStr = today.toISOString().split('T')[0]
    return dateStr === todayStr
  }

  const getCurrentMonthName = () => {
    const [year, month] = currentMonth.split('-').map(Number)
    return `${monthNames[month - 1]} ${year}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
      <div className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                href="/"
                className="text-slate-400 hover:text-white transition-colors flex items-center space-x-2"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Back</span>
              </Link>
              <div className="h-6 w-px bg-slate-700"></div>
              <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
                <Calendar className="w-6 h-6 text-blue-400" />
                <span>NBA Schedule</span>
              </h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-slate-700/50">
          <div className="flex items-center justify-between">
            <button
              onClick={() => changeMonth('prev')}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              <span>Previous</span>
            </button>
            
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white mb-1">
                {getCurrentMonthName()}
              </h2>
              <p className="text-slate-400 text-sm">
                {dates.length} game days • {Object.values(gamesByDate).flat().length} games
              </p>
            </div>

            <button
              onClick={() => changeMonth('next')}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={fetchSchedule}
            className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-slate-400 mt-4">Loading schedule...</p>
          </div>
        )}

        {!loading && dates.length === 0 && (
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-12 text-center border border-slate-700/50">
            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Games Scheduled</h3>
            <p className="text-slate-400">There are no games scheduled for {getCurrentMonthName()}</p>
          </div>
        )}

        {!loading && dates.map((date) => {
          const games = gamesByDate[date] || []
          const today = isToday(date)
          
          return (
            <div key={date} className="mb-8">
              <div className={`flex items-center space-x-3 mb-4 pb-2 border-b ${
                today 
                  ? 'border-blue-500/50' 
                  : 'border-slate-700/50'
              }`}>
                <div className={`px-4 py-2 rounded-lg font-semibold ${
                  today 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/50' 
                    : 'bg-slate-700/50 text-slate-200'
                }`}>
                  {today ? 'TODAY' : formatDate(date)}
                </div>
                <span className="text-slate-400 text-sm">
                  {games.length} {games.length === 1 ? 'game' : 'games'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {games.map((game) => (
                  <Link
                    key={game.game_id}
                    href={`/predictions?date=${date}`}
                    className="block"
                  >
                    <div className="bg-slate-800/80 hover:bg-slate-800 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-200 group">
                      <div className="flex items-center space-x-2 mb-4">
                        <Clock className="w-4 h-4 text-blue-400" />
                        <span className="text-slate-400 text-sm">{game.game_time}</span>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <MapPin className="w-4 h-4 text-slate-500" />
                            <span className="text-white font-semibold text-lg">
                              {game.away_team}
                            </span>
                          </div>
                          <span className="text-slate-500 text-sm">Away</span>
                        </div>

                        <div className="flex items-center">
                          <div className="flex-1 h-px bg-slate-700/50"></div>
                          <span className="px-3 text-slate-500 text-xs font-semibold">VS</span>
                          <div className="flex-1 h-px bg-slate-700/50"></div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <MapPin className="w-4 h-4 text-blue-400" />
                            <span className="text-white font-semibold text-lg">
                              {game.home_team}
                            </span>
                          </div>
                          <span className="text-blue-400 text-sm">Home</span>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-slate-700/50">
                        <span className="text-blue-400 text-sm group-hover:text-blue-300 transition-colors flex items-center justify-center">
                          View Prediction
                          <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
