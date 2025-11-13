"use client"

import { useEffect, useState } from "react"
import { NavHeader } from "@/components/nav-header"
import { RefreshCw, Activity, Clock, TrendingUp, AlertCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface Team {
  id: number
  name: string
  abbreviation: string
  score: number
  timeouts: number
}

interface LiveGame {
  id: string
  homeTeam: Team
  awayTeam: Team
  quarter: number
  time: string
  homeWinProbability: number
  lastUpdated: string
  scoreHistory: Array<{ time: string; homeScore: number; awayScore: number }>
}

const mockLiveGames: LiveGame[] = [
  {
    id: "game-1",
    homeTeam: { id: 1, name: "Los Angeles Lakers", abbreviation: "LAL", score: 58, timeouts: 2 },
    awayTeam: { id: 2, name: "Boston Celtics", abbreviation: "BOS", score: 55, timeouts: 3 },
    quarter: 2,
    time: "6:24",
    homeWinProbability: 0.62,
    lastUpdated: "2:14 PM",
    scoreHistory: [
      { time: "Q1", homeScore: 28, awayScore: 25 },
      { time: "Q2-4m", homeScore: 58, awayScore: 55 }
    ]
  },
  {
    id: "game-2",
    homeTeam: { id: 3, name: "Golden State Warriors", abbreviation: "GSW", score: 45, timeouts: 3 },
    awayTeam: { id: 4, name: "Denver Nuggets", abbreviation: "DEN", score: 48, timeouts: 2 },
    quarter: 2,
    time: "3:10",
    homeWinProbability: 0.38,
    lastUpdated: "2:08 PM",
    scoreHistory: [
      { time: "Q1", homeScore: 24, awayScore: 26 },
      { time: "Q2-8m", homeScore: 45, awayScore: 48 }
    ]
  }
]

export default function LivePage() {
  const [games, setGames] = useState<LiveGame[]>(mockLiveGames)
  const [selectedGame, setSelectedGame] = useState<LiveGame | null>(mockLiveGames[0])
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
      <NavHeader />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 flex items-center space-x-3">
              <Activity className="w-8 h-8 text-blue-400" />
              <span>Live Games</span>
            </h1>
            <p className="text-slate-400">Real-time game tracking and win probability updates</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            {selectedGame && (
              <Card className="bg-slate-800/60 border-slate-700/50 overflow-hidden">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-white mb-2">
                        {selectedGame.awayTeam.abbreviation} @ {selectedGame.homeTeam.abbreviation}
                      </h2>
                      <div className="flex items-center space-x-4 text-slate-400">
                        <span className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>Q{selectedGame.quarter} - {selectedGame.time}</span>
                        </span>
                        <span>{selectedGame.lastUpdated}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6 mb-8">
                    <div className="bg-slate-900/50 rounded-lg p-6">
                      <div className="text-slate-400 text-sm mb-2">{selectedGame.awayTeam.name}</div>
                      <div className="text-5xl font-bold text-white">{selectedGame.awayTeam.score}</div>
                    </div>
                    <div className="bg-blue-600/20 rounded-lg p-6 border border-blue-500/30">
                      <div className="text-blue-400 text-sm mb-2">{selectedGame.homeTeam.name}</div>
                      <div className="text-5xl font-bold text-blue-400">{selectedGame.homeTeam.score}</div>
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded-lg p-6 mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-white font-semibold flex items-center space-x-2">
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        <span>Win Probability</span>
                      </h3>
                    </div>
                    <div className="flex items-end space-x-4">
                      <div className="flex-1">
                        <div className="text-slate-400 text-sm mb-2">{selectedGame.awayTeam.abbreviation}</div>
                        <div className="w-full bg-slate-700/50 rounded-full h-8 overflow-hidden">
                          <div 
                            className="bg-slate-500 h-full flex items-center justify-center text-white font-semibold text-sm"
                            style={{ width: `${(1 - selectedGame.homeWinProbability) * 100}%` }}
                          >
                            {((1 - selectedGame.homeWinProbability) * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="text-blue-400 text-sm mb-2">{selectedGame.homeTeam.abbreviation}</div>
                        <div className="w-full bg-slate-700/50 rounded-full h-8 overflow-hidden">
                          <div 
                            className="bg-blue-600 h-full flex items-center justify-center text-white font-semibold text-sm"
                            style={{ width: `${selectedGame.homeWinProbability * 100}%` }}
                          >
                            {(selectedGame.homeWinProbability * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-white font-semibold mb-4">Score History</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={selectedGame.scoreHistory}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.2)" />
                        <XAxis dataKey="time" stroke="rgba(148,163,184,0.6)" />
                        <YAxis stroke="rgba(148,163,184,0.6)" />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'rgba(15,23,42,0.9)',
                            border: '1px solid rgba(100,116,139,0.5)',
                            borderRadius: '8px'
                          }}
                          formatter={(value) => value}
                          labelStyle={{ color: '#fff' }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="awayScore" 
                          stroke="rgba(148,163,184,0.8)" 
                          dot={{ fill: 'rgba(148,163,184,0.8)' }}
                          name={selectedGame.awayTeam.abbreviation}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="homeScore" 
                          stroke="#3b82f6" 
                          dot={{ fill: '#3b82f6' }}
                          name={selectedGame.homeTeam.abbreviation}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </Card>
            )}
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Live Games</h3>
            <div className="space-y-3">
              {games.map((game) => (
                <button
                  key={game.id}
                  onClick={() => setSelectedGame(game)}
                  className={`w-full text-left p-4 rounded-lg transition-all ${
                    selectedGame?.id === game.id
                      ? 'bg-blue-600 border border-blue-500'
                      : 'bg-slate-800/60 border border-slate-700/50 hover:border-slate-600/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-white">
                      {game.awayTeam.abbreviation} @ {game.homeTeam.abbreviation}
                    </div>
                    <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">
                      Q{game.quarter}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className={selectedGame?.id === game.id ? 'text-white' : 'text-slate-400'}>
                      {game.awayTeam.score} - {game.homeTeam.score}
                    </span>
                    <span className={`flex items-center space-x-1 ${selectedGame?.id === game.id ? 'text-white' : 'text-blue-400'}`}>
                      <TrendingUp className="w-4 h-4" />
                      <span>{(game.homeWinProbability * 100).toFixed(0)}%</span>
                    </span>
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-6 p-4 bg-blue-600/20 border border-blue-500/30 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-blue-400 mb-1">Real-Time Updates</h4>
                  <p className="text-sm text-blue-300">Win probabilities update every 30 seconds during live games</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12">
          <Link href="/predictions" className="text-blue-400 hover:text-blue-300 transition-colors flex items-center space-x-2">
            <span>←</span>
            <span>Back to Predictions</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
