"use client""use client""use client""use client""use client"



import { useState, useEffect } from "react"

import Link from "next/link"

import { ArrowLeft, Calendar, ChevronLeft, ChevronRight, RefreshCw, Clock, MapPin } from "lucide-react"import { useState, useEffect } from "react"



interface Game {import Link from "next/link"

  game_id: string

  date: stringimport { ArrowLeft, Calendar, ChevronLeft, ChevronRight, RefreshCw, Clock, MapPin } from "lucide-react"import { useState, useEffect } from "react"

  home_team: string

  away_team: string

  game_time: string

  season: stringinterface Game {import Link from "next/link"

}

  game_id: string

interface GamesByDate {

  [date: string]: Game[]  date: stringimport { ArrowLeft, Calendar, ChevronLeft, ChevronRight, RefreshCw, Clock, MapPin } from "lucide-react"import { useEffect, useState } from "react"import { useState } from "react"

}

  home_team: string

export default function SchedulePage() {

  const [gamesByDate, setGamesByDate] = useState<GamesByDate>({})  away_team: string

  const [dates, setDates] = useState<string[]>([])

  const [loading, setLoading] = useState(true)  game_time: string

  const [currentMonth, setCurrentMonth] = useState<string>(new Date().toISOString().slice(0, 7))

    season: stringinterface Game {import { Calendar, ChevronLeft, ChevronRight, RefreshCw, AlertCircle } from "lucide-react"import Link from "next/link"

  const monthNames = [

    "January", "February", "March", "April", "May", "June",}

    "July", "August", "September", "October", "November", "December"

  ]  game_id: string



  useEffect(() => {interface GamesByDate {

    fetchSchedule()

  }, [currentMonth])  [date: string]: Game[]  date: stringimport Link from "next/link"import { ArrowLeft, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react"



  const fetchSchedule = async () => {}

    try {

      setLoading(true)  home_team: string

      const response = await fetch(`/api/schedule?month=${currentMonth}`)

      const data = await response.json()export default function SchedulePage() {

      

      if (data.error) {  const [gamesByDate, setGamesByDate] = useState<GamesByDate>({})  away_team: stringimport { Card } from "@/components/ui/card"

        console.error('Error fetching schedule:', data.error)

        return  const [dates, setDates] = useState<string[]>([])

      }

  const [loading, setLoading] = useState(true)  game_time: string

      setGamesByDate(data.games_by_date || {})

      setDates(data.dates || [])  const [currentMonth, setCurrentMonth] = useState<string>(new Date().toISOString().slice(0, 7))

    } catch (error) {

      console.error('Error:', error)  season: stringinterface Team {

    } finally {

      setLoading(false)  const fetchSchedule = async (month: string) => {

    }

  }    setLoading(true)}



  const changeMonth = (direction: 'prev' | 'next') => {    try {

    const [year, month] = currentMonth.split('-').map(Number)

    let newYear = year      const response = await fetch(`/api/schedule?month=${month}`)  id: numberconst mockGames = [

    let newMonth = month

      const data = await response.json()

    if (direction === 'prev') {

      newMonth -= 1      interface GamesByDate {

      if (newMonth < 1) {

        newMonth = 12      if (data.success) {

        newYear -= 1

      }        setGamesByDate(data.gamesByDate || {})  [date: string]: Game[]  name: string  {

    } else {

      newMonth += 1        setDates(data.dates || [])

      if (newMonth > 12) {

        newMonth = 1      }}

        newYear += 1

      }    } catch (error) {

    }

      console.error('Failed to fetch schedule:', error)  abbreviation: string    id: "1",

    setCurrentMonth(`${newYear}-${String(newMonth).padStart(2, '0')}`)

  }    } finally {



  const formatDate = (dateStr: string) => {      setLoading(false)export default function SchedulePage() {

    const date = new Date(dateStr + 'T00:00:00')

    return date.toLocaleDateString('en-US', {     }

      weekday: 'short',

      month: 'short',   }  const [gamesByDate, setGamesByDate] = useState<GamesByDate>({})  score: number    date: "2025-10-27",

      day: 'numeric',

      year: 'numeric'

    })

  }  useEffect(() => {  const [dates, setDates] = useState<string[]>([])



  const isToday = (dateStr: string) => {    fetchSchedule(currentMonth)

    const today = new Date()

    today.setHours(today.getHours() - 8) // Adjust to PST  }, [currentMonth])  const [loading, setLoading] = useState(true)}    time: "7:30 PM ET",

    const todayStr = today.toISOString().split('T')[0]

    return dateStr === todayStr

  }

  const changeMonth = (direction: 'prev' | 'next') => {  const [currentMonth, setCurrentMonth] = useState<string>(new Date().toISOString().slice(0, 7))

  const getCurrentMonthName = () => {

    const [year, month] = currentMonth.split('-').map(Number)    const [year, month] = currentMonth.split('-').map(Number)

    return `${monthNames[month - 1]} ${year}`

  }    let newYear = year    homeTeam: "Los Angeles Lakers",



  return (    let newMonth = month

    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">

      {/* Header */}  const fetchSchedule = async (month: string) => {

      <div className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-10">

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">    if (direction === 'prev') {

          <div className="flex items-center justify-between">

            <div className="flex items-center space-x-4">      newMonth--    setLoading(true)interface Game {    awayTeam: "Boston Celtics",

              <Link 

                href="/"      if (newMonth < 1) {

                className="text-slate-400 hover:text-white transition-colors flex items-center space-x-2"

              >        newMonth = 12    try {

                <ArrowLeft className="w-5 h-5" />

                <span className="text-sm font-medium">Back</span>        newYear--

              </Link>

              <div className="h-6 w-px bg-slate-700"></div>      }      const response = await fetch(`/api/schedule?month=${month}`)  game_id: string    homeWinProb: 0.4,

              <h1 className="text-2xl font-bold text-white flex items-center space-x-2">

                <Calendar className="w-6 h-6 text-blue-400" />    } else {

                <span>NBA Schedule</span>

              </h1>      newMonth++      const data = await response.json()

            </div>

          </div>      if (newMonth > 12) {

        </div>

      </div>        newMonth = 1        date: string    awayWinProb: 0.6,



      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">        newYear++

        {/* Month Navigation */}

        <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-slate-700/50">      }      if (data.success) {

          <div className="flex items-center justify-between">

            <button    }

              onClick={() => changeMonth('prev')}

              className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors"        setGamesByDate(data.gamesByDate || {})  status: string    homeElo: 1620,

            >

              <ChevronLeft className="w-5 h-5" />    setCurrentMonth(`${newYear}-${String(newMonth).padStart(2, '0')}`)

              <span>Previous</span>

            </button>  }        setDates(data.dates || [])

            

            <div className="text-center">

              <h2 className="text-2xl font-bold text-white mb-1">

                {getCurrentMonthName()}  const formatDate = (dateStr: string) => {      }  home_team: Team    awayElo: 1650,

              </h2>

              <p className="text-slate-400 text-sm">    const date = new Date(dateStr + 'T00:00:00')

                {dates.length} game days • {Object.values(gamesByDate).flat().length} games

              </p>    return date.toLocaleDateString('en-US', {     } catch (error) {

            </div>

      weekday: 'short',

            <button

              onClick={() => changeMonth('next')}      month: 'short',       console.error('Failed to fetch schedule:', error)  visitor_team: Team    homeRecord: "25-15",

              className="flex items-center space-x-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors"

            >      day: 'numeric',

              <span>Next</span>

              <ChevronRight className="w-5 h-5" />      year: 'numeric'    } finally {

            </button>

          </div>    })



          <button  }      setLoading(false)}    awayRecord: "28-12",

            onClick={fetchSchedule}

            className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"

          >

            <RefreshCw className="w-4 h-4" />  const formatMonthYear = (monthStr: string) => {    }

            <span>Refresh</span>

          </button>    const [year, month] = monthStr.split('-')

        </div>

    const date = new Date(parseInt(year), parseInt(month) - 1)  }    confidence: "medium",

        {/* Loading State */}

        {loading && (    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

          <div className="text-center py-12">

            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>  }

            <p className="text-slate-400 mt-4">Loading schedule...</p>

          </div>

        )}

  const isToday = (dateStr: string) => {  useEffect(() => {interface GamesResponse {  },

        {/* Games by Date */}

        {!loading && dates.length === 0 && (    const today = new Date()

          <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-12 text-center border border-slate-700/50">

            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />    today.setHours(today.getHours() - 8) // Adjust to PST    fetchSchedule(currentMonth)

            <h3 className="text-xl font-semibold text-white mb-2">No Games Scheduled</h3>

            <p className="text-slate-400">There are no games scheduled for {getCurrentMonthName()}</p>    const todayStr = today.toISOString().split('T')[0]

          </div>

        )}    return dateStr === todayStr  }, [currentMonth])  success: boolean  {



        {!loading && dates.map((date) => {  }

          const games = gamesByDate[date] || []

          const today = isToday(date)

          

          return (  return (

            <div key={date} className="mb-8">

              {/* Date Header - FIXED: Better contrast and visibility */}    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">  const changeMonth = (direction: 'prev' | 'next') => {  count: number    id: "2",

              <div className={`flex items-center space-x-3 mb-4 pb-2 border-b ${

                today       {/* Navigation Bar */}

                  ? 'border-blue-500/50' 

                  : 'border-slate-700/50'      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-slate-700/50">    const [year, month] = currentMonth.split('-').map(Number)

              }`}>

                <div className={`px-4 py-2 rounded-lg ${        <div className="container mx-auto px-6 py-4">

                  today 

                    ? 'bg-blue-600 text-white font-bold'           <div className="flex items-center justify-between">    let newYear = year  games: Game[]    date: "2025-10-27",

                    : 'bg-slate-800/60 text-slate-300'

                }`}>            <div className="flex items-center gap-8">

                  {today ? 'TODAY' : formatDate(date)}

                </div>              <Link href="/" className="flex items-center gap-3 group">    let newMonth = month

                <span className="text-slate-400 text-sm">

                  {games.length} {games.length === 1 ? 'game' : 'games'}                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">

                </span>

              </div>                  🏀}    time: "8:00 PM ET",



              {/* Games Grid */}                </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                {games.map((game) => (                <span className="text-xl font-bold text-white">NBA Intel</span>    if (direction === 'prev') {

                  <Link

                    key={game.game_id}              </Link>

                    href={`/predictions?date=${date}`}

                    className="block"              <div className="hidden md:flex items-center gap-6">      newMonth--    homeTeam: "Golden State Warriors",

                  >

                    <div className="bg-slate-800/80 hover:bg-slate-800 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-200 group">                <Link href="/" className="text-slate-300 hover:text-white transition-colors flex items-center gap-2">

                      {/* Time */}

                      <div className="flex items-center space-x-2 mb-4">                  <ArrowLeft className="w-4 h-4" />      if (newMonth < 1) {

                        <Clock className="w-4 h-4 text-blue-400" />

                        <span className="text-slate-400 text-sm">{game.game_time}</span>                  Back to Home

                      </div>

                </Link>        newMonth = 12export default function SchedulePage() {    awayTeam: "Milwaukee Bucks",

                      {/* Teams */}

                      <div className="space-y-3">                <Link href="/predictions" className="text-slate-300 hover:text-blue-400 transition-colors">

                        {/* Away Team */}

                        <div className="flex items-center justify-between">                  Predictions        newYear--

                          <div className="flex items-center space-x-3">

                            <MapPin className="w-4 h-4 text-slate-500" />                </Link>

                            <span className="text-white font-semibold text-lg">

                              {game.away_team}                <Link href="/live" className="text-slate-300 hover:text-blue-400 transition-colors">      }  const [games, setGames] = useState<Game[]>([])    homeWinProb: 0.55,

                            </span>

                          </div>                  Live

                          <span className="text-slate-500 text-sm">Away</span>

                        </div>                </Link>    } else {



                        {/* VS Divider */}              </div>

                        <div className="flex items-center">

                          <div className="flex-1 h-px bg-slate-700/50"></div>            </div>      newMonth++  const [loading, setLoading] = useState(true)    awayWinProb: 0.45,

                          <span className="px-3 text-slate-500 text-xs font-semibold">VS</span>

                          <div className="flex-1 h-px bg-slate-700/50"></div>            <button

                        </div>

              onClick={() => fetchSchedule(currentMonth)}      if (newMonth > 12) {

                        {/* Home Team */}

                        <div className="flex items-center justify-between">              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"

                          <div className="flex items-center space-x-3">

                            <MapPin className="w-4 h-4 text-blue-400" />            >        newMonth = 1  const [error, setError] = useState<string | null>(null)    homeElo: 1640,

                            <span className="text-white font-semibold text-lg">

                              {game.home_team}              <RefreshCw className="w-5 h-5" />

                            </span>

                          </div>            </button>        newYear++

                          <span className="text-blue-400 text-sm">Home</span>

                        </div>          </div>

                      </div>

        </div>      }  const [currentDate, setCurrentDate] = useState<Date>(new Date())    awayElo: 1625,

                      {/* View Prediction Link */}

                      <div className="mt-4 pt-4 border-t border-slate-700/50">      </nav>

                        <span className="text-blue-400 text-sm group-hover:text-blue-300 transition-colors flex items-center justify-center">

                          View Prediction    }

                          <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">

                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />      {/* Header */}

                          </svg>

                        </span>      <div className="container mx-auto px-6 py-12">    homeRecord: "27-13",

                      </div>

                    </div>        <div className="text-center mb-12">

                  </Link>

                ))}          <div className="flex items-center justify-center gap-4 mb-6">    setCurrentMonth(`${newYear}-${String(newMonth).padStart(2, '0')}`)

              </div>

            </div>            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/50">

          )

        })}              <Calendar className="w-10 h-10 text-white" />  }  const fetchGames = async (date: Date) => {    awayRecord: "26-14",

      </div>

    </div>            </div>

  )

}          </div>


          <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">

            NBA Schedule  const formatDate = (dateStr: string) => {    setLoading(true)    confidence: "high",

          </h1>

          <p className="text-xl text-slate-300">    const date = new Date(dateStr + 'T00:00:00')

            Complete 2024-25 Season Schedule

          </p>    return date.toLocaleDateString('en-US', {     setError(null)  },

        </div>

      weekday: 'short',

        {/* Month Navigator */}

        <div className="flex items-center justify-center gap-6 mb-12">      month: 'short',   {

          <button

            onClick={() => changeMonth('prev')}      day: 'numeric',

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"

          >      year: 'numeric'    try {    id: "3",

            <ChevronLeft className="w-6 h-6" />

          </button>    })

          <div className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-2xl shadow-lg">

            {formatMonthYear(currentMonth)}  }      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"    date: "2025-10-27",

          </div>

          <button

            onClick={() => changeMonth('next')}

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"  const formatMonthYear = (monthStr: string) => {      const dateStr = date.toISOString().split('T')[0]    time: "9:30 PM ET",

          >

            <ChevronRight className="w-6 h-6" />    const [year, month] = monthStr.split('-')

          </button>

        </div>    const date = new Date(parseInt(year), parseInt(month) - 1)      const response = await fetch(`${backendUrl}/api/games?date=${dateStr}`)    homeTeam: "Phoenix Suns",



        {/* Loading State */}    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

        {loading && (

          <div className="text-center py-20">  }    awayTeam: "Denver Nuggets",

            <div className="inline-block w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>

            <p className="mt-4 text-slate-400">Loading schedule...</p>

          </div>

        )}  const isToday = (dateStr: string) => {      if (!response.ok) {    homeWinProb: 0.48,



        {/* Games by Date */}    const today = new Date().toISOString().split('T')[0]

        {!loading && dates.length === 0 && (

          <div className="text-center py-20">    return dateStr === today        throw new Error(`HTTP error! status: ${response.status}`)    awayWinProb: 0.52,

            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />

            <p className="text-xl text-slate-400">No games scheduled for this month</p>  }

          </div>

        )}      }    homeElo: 1630,



        {!loading && dates.length > 0 && (  return (

          <div className="space-y-8">

            {dates.map((date) => (    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">    awayElo: 1635,

              <div key={date} className="space-y-4">

                {/* Date Header */}      {/* Navigation Bar */}

                <div className={`flex items-center gap-4 px-6 py-4 rounded-xl ${

                  isToday(date)      <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-slate-700/50">      const data: GamesResponse = await response.json()    homeRecord: "26-14",

                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 shadow-lg shadow-green-500/30'

                    : 'bg-slate-800/80'        <div className="container mx-auto px-6 py-4">

                }`}>

                  <Calendar className="w-6 h-6 text-white" />          <div className="flex items-center justify-between">      setGames(data.games || [])    awayRecord: "27-13",

                  <h2 className="text-2xl font-bold text-white">

                    {formatDate(date)}            <div className="flex items-center gap-8">

                    {isToday(date) && (

                      <span className="ml-3 text-sm font-semibold bg-white/20 px-3 py-1 rounded-full">              <Link href="/" className="flex items-center gap-3 group">    } catch (err) {    confidence: "low",

                        TODAY

                      </span>                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">

                    )}

                  </h2>                  🏀      setError(err instanceof Error ? err.message : "Failed to fetch games")  },

                  <span className="ml-auto text-slate-300 font-semibold">

                    {gamesByDate[date]?.length || 0} games                </div>

                  </span>

                </div>                <span className="text-xl font-bold text-white">NBA Intel</span>      console.error("Error:", err)]



                {/* Games Grid */}              </Link>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                  {gamesByDate[date]?.map((game) => (              <div className="hidden md:flex items-center gap-6">    } finally {

                    <div

                      key={game.game_id}                <Link href="/" className="text-slate-300 hover:text-white transition-colors flex items-center gap-2">

                      className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/20"

                    >                  <ArrowLeft className="w-4 h-4" />      setLoading(false)export default function SchedulePage() {

                      {/* Game Time */}

                      <div className="flex items-center gap-2 mb-4 text-slate-400">                  Back to Home

                        <Clock className="w-4 h-4" />

                        <span className="text-sm font-medium">{game.game_time}</span>                </Link>    }  const [selectedDate, setSelectedDate] = useState("2025-10-27")

                      </div>

                <Link href="/predictions" className="text-slate-300 hover:text-blue-400 transition-colors">

                      {/* Teams */}

                      <div className="space-y-3">                  Predictions  }

                        {/* Away Team */}

                        <div className="flex items-center justify-between">                </Link>

                          <div className="flex items-center gap-3">

                            <MapPin className="w-4 h-4 text-slate-500" />                <Link href="/live" className="text-slate-300 hover:text-blue-400 transition-colors">  return (

                            <span className="text-slate-400 text-sm">@</span>

                            <span className="text-2xl font-bold text-white">                  Live

                              {game.away_team}

                            </span>                </Link>  useEffect(() => {    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/5">

                          </div>

                        </div>              </div>



                        {/* VS Divider */}            </div>    fetchGames(currentDate)      <header className="glass-strong sticky top-0 z-50 border-b">

                        <div className="flex items-center gap-2">

                          <div className="h-px bg-slate-700 flex-1"></div>            <button

                          <span className="text-slate-500 text-xs font-semibold">VS</span>

                          <div className="h-px bg-slate-700 flex-1"></div>              onClick={() => fetchSchedule(currentMonth)}  }, [currentDate])        <div className="container mx-auto px-6 py-6 flex items-center justify-between">

                        </div>

              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"

                        {/* Home Team */}

                        <div className="flex items-center justify-between">            >          <Link href="/" className="flex items-center gap-3 group">

                          <div className="flex items-center gap-3">

                            <div className="w-4 h-4 rounded-full bg-blue-500"></div>              <RefreshCw className="w-5 h-5" />

                            <span className="text-2xl font-bold text-white">

                              {game.home_team}            </button>  const goToPreviousDay = () => {            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-3xl glow-lg group-hover:scale-110 transition-transform duration-300">

                            </span>

                          </div>          </div>

                        </div>

                      </div>        </div>    const prevDay = new Date(currentDate)              🏀



                      {/* View Prediction Button */}      </nav>

                      <Link

                        href={`/predictions?date=${date}`}    prevDay.setDate(prevDay.getDate() - 1)            </div>

                        className="mt-4 w-full py-2 px-4 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-sm font-semibold text-center block transition-all"

                      >      {/* Header */}

                        View Prediction

                      </Link>      <div className="container mx-auto px-6 py-12">    setCurrentDate(prevDay)            <div>

                    </div>

                  ))}        <div className="text-center mb-12">

                </div>

              </div>          <div className="flex items-center justify-center gap-4 mb-6">  }              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

            ))}

          </div>            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/50">

        )}

      </div>              <Calendar className="w-10 h-10 text-white" />                NBA Intel



      {/* Quick Stats Footer */}            </div>

      <div className="container mx-auto px-6 py-12 mt-12">

        <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">          </div>  const goToNextDay = () => {              </h1>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">

            <div>          <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">

              <div className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">

                {dates.length}            NBA Schedule    const nextDay = new Date(currentDate)              <p className="text-xs text-muted-foreground font-medium">ML-Powered Analytics</p>

              </div>

              <div className="text-slate-400">Game Days This Month</div>          </h1>

            </div>

            <div>          <p className="text-xl text-slate-300">    nextDay.setDate(nextDay.getDate() + 1)            </div>

              <div className="text-4xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">

                {Object.values(gamesByDate).flat().length}            Complete 2024-25 Season Schedule

              </div>

              <div className="text-slate-400">Total Games</div>          </p>    setCurrentDate(nextDay)          </Link>

            </div>

            <div>        </div>

              <div className="text-4xl font-black bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent mb-2">

                2024-25  }          <nav className="hidden md:flex items-center gap-8">

              </div>

              <div className="text-slate-400">NBA Season</div>        {/* Month Navigator */}

            </div>

          </div>        <div className="flex items-center justify-center gap-6 mb-12">            <Link href="/schedule" className="text-sm font-semibold text-primary relative">

        </div>

      </div>          <button

    </div>

  )            onClick={() => changeMonth('prev')}  const goToToday = () => {              Schedule

}

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"

          >    setCurrentDate(new Date())              <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary" />

            <ChevronLeft className="w-6 h-6" />

          </button>  }            </Link>

          <div className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-2xl shadow-lg">

            {formatMonthYear(currentMonth)}            <Link href="/live" className="text-sm font-semibold hover:text-primary transition-colors">

          </div>

          <button  const formatDate = (date: Date) => {              Live

            onClick={() => changeMonth('next')}

            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"    const today = new Date()            </Link>

          >

            <ChevronRight className="w-6 h-6" />    const tomorrow = new Date(today)            <Link href="/chemistry" className="text-sm font-semibold hover:text-primary transition-colors">

          </button>

        </div>    tomorrow.setDate(tomorrow.getDate() + 1)              Chemistry



        {/* Loading State */}    const yesterday = new Date(today)            </Link>

        {loading && (

          <div className="text-center py-20">    yesterday.setDate(yesterday.getDate() - 1)            <Link href="/sentiment" className="text-sm font-semibold hover:text-primary transition-colors">

            <div className="inline-block w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>

            <p className="mt-4 text-slate-400">Loading schedule...</p>              Sentiment

          </div>

        )}    const dateStr = date.toISOString().split('T')[0]            </Link>



        {/* Games by Date */}    const todayStr = today.toISOString().split('T')[0]            <Link href="/postgame" className="text-sm font-semibold hover:text-primary transition-colors">

        {!loading && dates.length === 0 && (

          <div className="text-center py-20">    const tomorrowStr = tomorrow.toISOString().split('T')[0]              Analytics

            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />

            <p className="text-xl text-slate-400">No games scheduled for this month</p>    const yesterdayStr = yesterday.toISOString().split('T')[0]            </Link>

          </div>

        )}          </nav>



        {!loading && dates.length > 0 && (    if (dateStr === todayStr) return "Today"        </div>

          <div className="space-y-8">

            {dates.map((date) => (    if (dateStr === tomorrowStr) return "Tomorrow"      </header>

              <div key={date} className="space-y-4">

                {/* Date Header */}    if (dateStr === yesterdayStr) return "Yesterday"

                <div className={`flex items-center gap-4 px-6 py-4 rounded-xl ${

                  isToday(date)      <main className="container mx-auto px-6 py-12">

                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 shadow-lg shadow-green-500/30'

                    : 'bg-slate-800/80'    return date.toLocaleDateString('en-US', {        <div className="mb-12">

                }`}>

                  <Calendar className="w-6 h-6 text-white" />      weekday: 'long',          <Link

                  <h2 className="text-2xl font-bold text-white">

                    {formatDate(date)}      month: 'long',            href="/"

                    {isToday(date) && (

                      <span className="ml-3 text-sm font-semibold bg-white/20 px-3 py-1 rounded-full">      day: 'numeric',            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6 group"

                        TODAY

                      </span>      year: 'numeric'          >

                    )}

                  </h2>    })            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />

                  <span className="ml-auto text-slate-300 font-semibold">

                    {gamesByDate[date]?.length || 0} games  }            <span className="font-medium">Back to Home</span>

                  </span>

                </div>          </Link>



                {/* Games Grid */}  const getStatusBadge = (status: string) => {

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                  {gamesByDate[date]?.map((game) => (    const isLive = status && (          <div className="flex items-center gap-4 mb-6">

                    <div

                      key={game.game_id}      status.toLowerCase().includes('live') ||            <Calendar className="w-12 h-12 text-primary glow" />

                      className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/20"

                    >      status.toLowerCase().includes('q') ||            <div>

                      {/* Game Time */}

                      <div className="flex items-center gap-2 mb-4 text-slate-400">      status.includes(':')              <h1 className="text-6xl font-black tracking-tight" style={{ fontFamily: "var(--font-display)" }}>

                        <Clock className="w-4 h-4" />

                        <span className="text-sm font-medium">{game.game_time}</span>    )                Game Schedule

                      </div>

    const isFinal = status && status.toLowerCase().includes('final')              </h1>

                      {/* Teams */}

                      <div className="space-y-3">              <p className="text-xl text-muted-foreground font-medium mt-2">ML-powered pregame analysis</p>

                        {/* Away Team */}

                        <div className="flex items-center justify-between">    if (isLive) {            </div>

                          <div className="flex items-center gap-3">

                            <MapPin className="w-4 h-4 text-slate-500" />      return (          </div>

                            <span className="text-slate-400 text-sm">@</span>

                            <span className="text-2xl font-bold text-white">        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">        </div>

                              {game.away_team}

                            </span>          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>

                          </div>

                        </div>          LIVE        <Card className="p-8 mb-12 glass-strong border-2">



                        {/* VS Divider */}        </span>          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">

                        <div className="flex items-center gap-2">

                          <div className="h-px bg-slate-700 flex-1"></div>      )            <div className="flex-1">

                          <span className="text-slate-500 text-xs font-semibold">VS</span>

                          <div className="h-px bg-slate-700 flex-1"></div>    } else if (isFinal) {              <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3 block">

                        </div>

      return (                Select Date

                        {/* Home Team */}

                        <div className="flex items-center justify-between">        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500/30">              </label>

                          <div className="flex items-center gap-3">

                            <div className="w-4 h-4 rounded-full bg-blue-500"></div>          FINAL              <input

                            <span className="text-2xl font-bold text-white">

                              {game.home_team}        </span>                type="date"

                            </span>

                          </div>      )                value={selectedDate}

                        </div>

                      </div>    } else {                onChange={(e) => setSelectedDate(e.target.value)}



                      {/* View Prediction Button */}      return (                className="w-full md:w-auto px-6 py-4 rounded-xl border-2 border-border bg-background text-foreground font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"

                      <Link

                        href={`/predictions?date=${date}`}        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">              />

                        className="mt-4 w-full py-2 px-4 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-sm font-semibold text-center block transition-all"

                      >          {status || 'SCHEDULED'}            </div>

                        View Prediction

                      </Link>        </span>            <div className="flex items-center gap-6 text-sm">

                    </div>

                  ))}      )              <div className="flex items-center gap-2">

                </div>

              </div>    }                <div className="w-3 h-3 rounded-full bg-primary" />

            ))}

          </div>  }                <span className="font-medium">High Confidence</span>

        )}

      </div>              </div>



      {/* Quick Stats Footer */}  return (              <div className="flex items-center gap-2">

      <div className="container mx-auto px-6 py-12 mt-12">

        <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950/20 to-gray-950 p-6">                <div className="w-3 h-3 rounded-full bg-secondary" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">

            <div>      {/* Header */}                <span className="font-medium">Medium Confidence</span>

              <div className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">

                {dates.length}      <div className="max-w-7xl mx-auto mb-8">              </div>

              </div>

              <div className="text-slate-400">Game Days This Month</div>        <div className="flex items-center justify-between mb-6">              <div className="flex items-center gap-2">

            </div>

            <div>          <div>                <div className="w-3 h-3 rounded-full bg-muted-foreground" />

              <div className="text-4xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">

                {Object.values(gamesByDate).flat().length}            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-600 bg-clip-text text-transparent mb-2 flex items-center gap-3">                <span className="font-medium">Low Confidence</span>

              </div>

              <div className="text-slate-400">Total Games</div>              <Calendar className="w-10 h-10 text-blue-500" />              </div>

            </div>

            <div>              NBA Schedule            </div>

              <div className="text-4xl font-black bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent mb-2">

                2024-25            </h1>          </div>

              </div>

              <div className="text-slate-400">NBA Season</div>            <p className="text-gray-400">        </Card>

            </div>

          </div>              Browse games by date and view predictions

        </div>

      </div>            </p>        <div className="space-y-6">

    </div>

  )          </div>          {mockGames.map((game) => (

}

            <Card

          <button              key={game.id}

            onClick={() => fetchGames(currentDate)}              className="p-8 glass-strong border-2 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group"

            disabled={loading}            >

            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"              <div className="flex items-center justify-between mb-6">

          >                <div className="flex items-center gap-3">

            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />                  <div

            Refresh                    className={`w-3 h-3 rounded-full ${

          </button>                      game.confidence === "high"

        </div>                        ? "bg-primary"

                        : game.confidence === "medium"

        {/* Date Navigation */}                          ? "bg-secondary"

        <div className="glass-strong rounded-2xl p-6 mb-6">                          : "bg-muted-foreground"

          <div className="flex items-center justify-between">                    } glow`}

            <button                  />

              onClick={goToPreviousDay}                  <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">{game.time}</span>

              className="p-2 hover:bg-white/10 rounded-lg transition-colors"                </div>

            >                <span

              <ChevronLeft className="w-6 h-6 text-gray-400" />                  className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${

            </button>                    game.confidence === "high"

                      ? "bg-primary/20 text-primary"

            <div className="flex items-center gap-4">                      : game.confidence === "medium"

              <div className="text-center">                        ? "bg-secondary/20 text-secondary"

                <p className="text-2xl font-bold text-white">{formatDate(currentDate)}</p>                        : "bg-muted text-muted-foreground"

                <p className="text-sm text-gray-500 mt-1">                  }`}

                  {currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}                >

                </p>                  {game.confidence} confidence

              </div>                </span>

              </div>

              {currentDate.toISOString().split('T')[0] !== new Date().toISOString().split('T')[0] && (

                <button              <div className="grid md:grid-cols-3 gap-8 items-center">

                  onClick={goToToday}                {/* Away Team */}

                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"                <div className="text-center md:text-right space-y-3">

                >                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>

                  Today                    {game.awayTeam}

                </button>                  </h3>

              )}                  <div className="flex items-center justify-center md:justify-end gap-4 text-sm text-muted-foreground">

            </div>                    <span className="font-semibold">{game.awayRecord}</span>

                    <span>•</span>

            <button                    <span className="font-semibold">Elo: {game.awayElo}</span>

              onClick={goToNextDay}                  </div>

              className="p-2 hover:bg-white/10 rounded-lg transition-colors"                  <div className="flex items-center justify-center md:justify-end gap-2">

            >                    <span className="text-5xl font-black text-primary">{(game.awayWinProb * 100).toFixed(0)}%</span>

              <ChevronRight className="w-6 h-6 text-gray-400" />                    {game.awayWinProb > 0.5 ? (

            </button>                      <TrendingUp className="w-8 h-8 text-primary" />

          </div>                    ) : game.awayWinProb < 0.5 ? (

        </div>                      <TrendingDown className="w-8 h-8 text-muted-foreground" />

                    ) : (

        {/* Stats Summary */}                      <Minus className="w-8 h-8 text-muted-foreground" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">                    )}

          <div className="glass-strong rounded-xl p-4">                  </div>

            <div className="flex items-center gap-3">                </div>

              <div className="p-2 bg-blue-500/20 rounded-lg">

                <Calendar className="w-5 h-5 text-blue-400" />                {/* VS Divider */}

              </div>                <div className="flex flex-col items-center justify-center">

              <div>                  <div

                <p className="text-2xl font-bold text-white">{games.length}</p>                    className="text-4xl font-black text-muted-foreground mb-4"

                <p className="text-sm text-gray-400">Games</p>                    style={{ fontFamily: "var(--font-display)" }}

              </div>                  >

            </div>                    VS

          </div>                  </div>

                  <div className="w-full h-3 bg-muted rounded-full overflow-hidden">

          <div className="glass-strong rounded-xl p-4">                    <div

            <div className="flex items-center gap-3">                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500"

              <div className="p-2 bg-red-500/20 rounded-lg">                      style={{ width: `${game.awayWinProb * 100}%` }}

                <div className="w-5 h-5 flex items-center justify-center">                    />

                  <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>                  </div>

                </div>                  <div className="mt-4 text-sm text-muted-foreground font-semibold">

              </div>                    Predicted Spread: {game.awayWinProb > game.homeWinProb ? "Away" : "Home"} by{" "}

              <div>                    {Math.abs((game.awayWinProb - game.homeWinProb) * 20).toFixed(1)}

                <p className="text-2xl font-bold text-white">                  </div>

                  {games.filter(g => g.status?.toLowerCase().includes('live') || g.status?.toLowerCase().includes('q')).length}                </div>

                </p>

                <p className="text-sm text-gray-400">Live</p>                {/* Home Team */}

              </div>                <div className="text-center md:text-left space-y-3">

            </div>                  <h3 className="text-3xl font-black" style={{ fontFamily: "var(--font-display)" }}>

          </div>                    {game.homeTeam}

                  </h3>

          <div className="glass-strong rounded-xl p-4">                  <div className="flex items-center justify-center md:justify-start gap-4 text-sm text-muted-foreground">

            <div className="flex items-center gap-3">                    <span className="font-semibold">{game.homeRecord}</span>

              <div className="p-2 bg-green-500/20 rounded-lg">                    <span>•</span>

                <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">                    <span className="font-semibold">Elo: {game.homeElo}</span>

                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />                  </div>

                </svg>                  <div className="flex items-center justify-center md:justify-start gap-2">

              </div>                    {game.homeWinProb > 0.5 ? (

              <div>                      <TrendingUp className="w-8 h-8 text-primary" />

                <p className="text-2xl font-bold text-white">                    ) : game.homeWinProb < 0.5 ? (

                  {games.filter(g => g.status?.toLowerCase().includes('final')).length}                      <TrendingDown className="w-8 h-8 text-muted-foreground" />

                </p>                    ) : (

                <p className="text-sm text-gray-400">Completed</p>                      <Minus className="w-8 h-8 text-muted-foreground" />

              </div>                    )}

            </div>                    <span className="text-5xl font-black text-primary">{(game.homeWinProb * 100).toFixed(0)}%</span>

          </div>                  </div>

        </div>                </div>

      </div>              </div>



      {/* Games List */}              {/* Key Factors */}

      <div className="max-w-7xl mx-auto">              <div className="mt-8 pt-8 border-t border-border">

        {loading && games.length === 0 ? (                <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Key Factors</h4>

          <div className="flex flex-col items-center justify-center py-20">                <div className="grid md:grid-cols-3 gap-4 text-sm">

            <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mb-4" />                  <div className="flex items-center gap-2">

            <p className="text-gray-400">Loading games...</p>                    <div className="w-2 h-2 rounded-full bg-primary" />

          </div>                    <span className="text-muted-foreground">

        ) : error ? (                      Home advantage: <span className="font-bold text-foreground">+3.2%</span>

          <div className="glass-strong rounded-2xl p-8 text-center">                    </span>

            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />                  </div>

            <p className="text-red-400 mb-2">Failed to load games</p>                  <div className="flex items-center gap-2">

            <p className="text-gray-500 text-sm">{error}</p>                    <div className="w-2 h-2 rounded-full bg-secondary" />

            <button                    <span className="text-muted-foreground">

              onClick={() => fetchGames(currentDate)}                      Recent form: <span className="font-bold text-foreground">+2.1%</span>

              className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"                    </span>

            >                  </div>

              Try Again                  <div className="flex items-center gap-2">

            </button>                    <div className="w-2 h-2 rounded-full bg-chart-3" />

          </div>                    <span className="text-muted-foreground">

        ) : games.length === 0 ? (                      Rest differential: <span className="font-bold text-foreground">+1.5%</span>

          <div className="glass-strong rounded-2xl p-12 text-center">                    </span>

            <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />                  </div>

            <p className="text-xl text-gray-400 mb-2">No games scheduled</p>                </div>

            <p className="text-gray-500">There are no NBA games on {formatDate(currentDate)}</p>              </div>

            <div className="flex gap-4 justify-center mt-6">            </Card>

              <button          ))}

                onClick={goToPreviousDay}        </div>

                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"      </main>

              >    </div>

                Previous Day  )

              </button>}

              <button
                onClick={goToNextDay}
                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Next Day
              </button>
            </div>
          </div>
        ) : (
          <div className="grid gap-4">
            {games.map((game, index) => (
              <div
                key={game.game_id || index}
                className="glass-strong rounded-2xl p-6 hover:bg-white/5 transition-all duration-200 group"
              >
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    {getStatusBadge(game.status)}
                    <span className="text-sm text-gray-500">
                      {new Date(game.date).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>

                  <Link
                    href={`/predictions/${game.game_id}`}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    View Prediction
                  </Link>
                </div>

                {/* Teams */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Away Team */}
                  <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold">
                        {game.visitor_team?.abbreviation || 'TBD'}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {game.visitor_team?.name || 'TBD'}
                        </p>
                        <p className="text-sm text-gray-500">Away</p>
                      </div>
                    </div>
                    {game.visitor_team?.score !== undefined && (
                      <div className="text-3xl font-bold text-white">
                        {game.visitor_team.score}
                      </div>
                    )}
                  </div>

                  {/* Home Team */}
                  <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center text-white font-bold">
                        {game.home_team?.abbreviation || 'TBD'}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {game.home_team?.name || 'TBD'}
                        </p>
                        <p className="text-sm text-gray-500">Home</p>
                      </div>
                    </div>
                    {game.home_team?.score !== undefined && (
                      <div className="text-3xl font-bold text-white">
                        {game.home_team.score}
                      </div>
                    )}
                  </div>
                </div>

                {/* Prediction Placeholder */}
                {(!game.status || game.status.toLowerCase().includes('scheduled')) && (
                  <div className="mt-6 pt-4 border-t border-gray-800">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Win Probability:</span>
                      <span className="text-blue-400">Coming soon...</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
