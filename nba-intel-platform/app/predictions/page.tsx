"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Activity, BarChart3,
    Brain,
    DollarSign,
    RefreshCw,
    Shield,
    Target,
    TrendingDown,
    TrendingUp,
    TrendingUpIcon,
    Zap
} from "lucide-react"
import { useEffect, useState } from "react"

interface StatPrediction {
  raw: number
  calibrated: number
  over: boolean
  confidence: number
}

interface PlayerPrediction {
  player_name: string
  predictions: {
    PTS: StatPrediction
    AST: StatPrediction
    REB: StatPrediction
    STL: StatPrediction
    BLK: StatPrediction
  }
  ready_for_production: boolean
  error: string | null
}

interface KellyRecommendation {
  stat: string
  edge: number
  kelly_fraction: number
  bet_amount: number
  recommendation: string
}

const statColors = {
  PTS: { bg: "bg-gradient-to-br from-red-500 to-red-600", text: "text-red-600", border: "border-red-500" },
  AST: { bg: "bg-gradient-to-br from-blue-500 to-blue-600", text: "text-blue-600", border: "border-blue-500" },
  REB: { bg: "bg-gradient-to-br from-green-500 to-green-600", text: "text-green-600", border: "border-green-500" },
  STL: { bg: "bg-gradient-to-br from-purple-500 to-purple-600", text: "text-purple-600", border: "border-purple-500" },
  BLK: { bg: "bg-gradient-to-br from-yellow-500 to-yellow-600", text: "text-yellow-600", border: "border-yellow-500" },
}

const statLabels = {
  PTS: "Points",
  AST: "Assists",
  REB: "Rebounds",
  STL: "Steals",
  BLK: "Blocks",
}

const statIcons = {
  PTS: Target,
  AST: Activity,
  REB: BarChart3,
  STL: Zap,
  BLK: Shield,
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<PlayerPrediction | null>(null)
  const [kellyRecs, setKellyRecs] = useState<KellyRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [playerName, setPlayerName] = useState("LeBron James")
  const [team, setTeam] = useState("LAL")
  const [opponent, setOpponent] = useState("GSW")
  const [gameDate, setGameDate] = useState("2024-10-26")
  const [bankroll, setBankroll] = useState(10000)

  const fetchPredictions = async () => {
    setLoading(true)
    setError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      
      // Fetch predictions
      const response = await fetch(`${backendUrl}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          player_name: playerName,
          game_date: gameDate,
          team: team,
          opponent: opponent,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setPredictions(data)

      // Fetch Kelly Criterion recommendations
      const kellyResponse = await fetch(`${backendUrl}/kelly`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bankroll: bankroll,
          kelly_fraction: 0.25,
          min_edge: 0.05,
          predictions: Object.fromEntries(
            Object.entries(data.predictions).map(([stat, pred]: [string, any]) => [
              stat,
              { calibrated: pred.calibrated }
            ])
          )
        }),
      })

      if (kellyResponse.ok) {
        const kellyData = await kellyResponse.json()
        if (kellyData.recommendations) {
          setKellyRecs(kellyData.recommendations)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch predictions")
      console.error("Error fetching predictions:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPredictions()
    const interval = setInterval(fetchPredictions, 30000)
    return () => clearInterval(interval)
  }, [])

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <Card className="border-red-500 bg-slate-800/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-red-500">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-white">{error}</p>
            <Button onClick={fetchPredictions} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loading && !predictions) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-purple-400 mx-auto mb-4" />
          <p className="text-white text-lg">Loading predictions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero Section */}
      <div className="border-b border-purple-500/20 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto p-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Brain className="h-10 w-10 text-purple-400" />
                <h1 className="text-5xl font-bold text-white">NBA Intelligence Platform</h1>
              </div>
              <p className="text-purple-200 text-lg">AI-Powered Predictions & Betting Analytics</p>
              <div className="flex gap-2 mt-3">
                <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/50">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
                  Live
                </Badge>
                <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/50">
                  5 Models Active
                </Badge>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/50">
                  Kelly Criterion
                </Badge>
              </div>
            </div>
            <Button 
              onClick={fetchPredictions} 
              disabled={loading} 
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              <RefreshCw className={`mr-2 h-5 w-5 ${loading ? "animate-spin" : ""}`} />
              Refresh Data
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto p-8">
        <Tabs defaultValue="predictions" className="space-y-8">
          <TabsList className="grid w-full md:w-auto md:inline-grid grid-cols-3 bg-slate-800/50 backdrop-blur">
            <TabsTrigger value="predictions" className="data-[state=active]:bg-purple-600">
              <Target className="h-4 w-4 mr-2" />
              Predictions
            </TabsTrigger>
            <TabsTrigger value="kelly" className="data-[state=active]:bg-purple-600">
              <DollarSign className="h-4 w-4 mr-2" />
              Betting
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-purple-600">
              <Activity className="h-4 w-4 mr-2" />
              Configure
            </TabsTrigger>
          </TabsList>

          {/* Predictions Tab */}
          <TabsContent value="predictions" className="space-y-6">
            {predictions && (
              <>
                {/* Player Info Card */}
                <Card className="bg-slate-800/50 backdrop-blur border-purple-500/20">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-3xl text-white">{predictions.player_name}</CardTitle>
                        <CardDescription className="text-purple-200 text-lg mt-2">
                          {team} vs {opponent} • {gameDate}
                        </CardDescription>
                      </div>
                      <Badge 
                        variant={predictions.ready_for_production ? "default" : "destructive"}
                        className="text-lg px-4 py-2"
                      >
                        {predictions.ready_for_production ? "✓ Production Ready" : "⚠ Not Ready"}
                      </Badge>
                    </div>
                  </CardHeader>
                </Card>

                {/* Stat Predictions Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
                  {Object.entries(predictions.predictions).map(([stat, prediction]) => {
                    const Icon = statIcons[stat as keyof typeof statIcons]
                    const colors = statColors[stat as keyof typeof statColors]
                    
                    return (
                      <Card 
                        key={stat} 
                        className={`bg-slate-800/50 backdrop-blur border-2 ${colors.border} hover:scale-105 transition-transform`}
                      >
                        <CardHeader className={`${colors.bg} text-white rounded-t-lg`}>
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <Icon className="h-6 w-6" />
                              <CardTitle className="text-xl">{statLabels[stat as keyof typeof statLabels]}</CardTitle>
                            </div>
                            {prediction.over ? (
                              <TrendingUp className="h-6 w-6" />
                            ) : (
                              <TrendingDown className="h-6 w-6" />
                            )}
                          </div>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-4">
                          {/* Prediction */}
                          <div className="text-center">
                            <p className="text-sm text-gray-400 mb-1">Prediction</p>
                            <p className={`text-3xl font-bold ${prediction.over ? 'text-green-400' : 'text-red-400'}`}>
                              {prediction.over ? "OVER" : "UNDER"}
                            </p>
                          </div>

                          {/* Confidence Bar */}
                          <div>
                            <div className="flex justify-between text-sm mb-2">
                              <span className="text-gray-400">Confidence</span>
                              <span className="text-white font-bold">
                                {(prediction.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <Progress 
                              value={prediction.confidence * 100} 
                              className="h-3"
                            />
                          </div>

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-700">
                            <div className="text-center">
                              <p className="text-xs text-gray-400">Raw</p>
                              <p className="font-bold text-white">{(prediction.raw * 100).toFixed(1)}%</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-gray-400">Calibrated</p>
                              <p className="font-bold text-white">{(prediction.calibrated * 100).toFixed(1)}%</p>
                            </div>
                          </div>

                          {/* Edge Indicator */}
                          <div className="pt-2 border-t border-gray-700">
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-gray-400">Edge</span>
                              <Badge variant="outline" className="bg-purple-500/10 text-purple-400">
                                {((prediction.confidence - 0.5) * 100).toFixed(1)}%
                              </Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>

                {/* Portfolio Summary */}
                <Card className="bg-gradient-to-br from-slate-800 to-purple-900/20 backdrop-blur border-purple-500/20">
                  <CardHeader>
                    <CardTitle className="text-2xl text-white flex items-center gap-2">
                      <TrendingUpIcon className="h-6 w-6 text-green-400" />
                      Portfolio Summary
                    </CardTitle>
                    <CardDescription className="text-purple-200">
                      Aggregate betting recommendations across all predictions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                      <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                        <p className="text-sm text-gray-400 mb-1">Total Predictions</p>
                        <p className="text-4xl font-bold text-white">5</p>
                      </div>
                      <div className="text-center p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                        <p className="text-sm text-gray-400 mb-1">OVER Picks</p>
                        <p className="text-4xl font-bold text-green-400">
                          {Object.values(predictions.predictions).filter((p) => p.over).length}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-red-500/10 rounded-lg border border-red-500/30">
                        <p className="text-sm text-gray-400 mb-1">UNDER Picks</p>
                        <p className="text-4xl font-bold text-red-400">
                          {Object.values(predictions.predictions).filter((p) => !p.over).length}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
                        <p className="text-sm text-gray-400 mb-1">Avg Confidence</p>
                        <p className="text-4xl font-bold text-purple-400">
                          {(
                            (Object.values(predictions.predictions).reduce(
                              (sum, p) => sum + p.confidence,
                              0
                            ) / 5) * 100
                          ).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-center p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                        <p className="text-sm text-gray-400 mb-1">Strong Edges</p>
                        <p className="text-4xl font-bold text-blue-400">
                          {Object.values(predictions.predictions).filter((p) => 
                            Math.abs(p.confidence - 0.5) > 0.15
                          ).length}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Kelly Criterion Tab */}
          <TabsContent value="kelly" className="space-y-6">
            <Card className="bg-slate-800/50 backdrop-blur border-purple-500/20">
              <CardHeader>
                <CardTitle className="text-2xl text-white flex items-center gap-2">
                  <DollarSign className="h-6 w-6 text-green-400" />
                  Kelly Criterion Betting Strategy
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Optimal bet sizing based on edge and bankroll management
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <p className="text-sm text-gray-400 mb-1">Total Bankroll</p>
                    <p className="text-3xl font-bold text-green-400">${bankroll.toLocaleString()}</p>
                  </div>
                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <p className="text-sm text-gray-400 mb-1">Kelly Fraction</p>
                    <p className="text-3xl font-bold text-purple-400">25%</p>
                  </div>
                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <p className="text-sm text-gray-400 mb-1">Min Edge</p>
                    <p className="text-3xl font-bold text-blue-400">5%</p>
                  </div>
                </div>

                {kellyRecs.length > 0 ? (
                  <div className="space-y-4">
                    {kellyRecs.map((rec, idx) => (
                      <Card key={idx} className="bg-slate-700/30 border-gray-700">
                        <CardContent className="pt-6">
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="text-lg font-bold text-white">{rec.stat}</p>
                              <p className="text-sm text-gray-400">{rec.recommendation}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-400">Recommended Bet</p>
                              <p className="text-2xl font-bold text-green-400">
                                ${rec.bet_amount.toFixed(2)}
                              </p>
                              <p className="text-xs text-purple-400">
                                Edge: {(rec.edge * 100).toFixed(2)}%
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-400">
                    <DollarSign className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p>No betting recommendations available. Fetch predictions first.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card className="bg-slate-800/50 backdrop-blur border-purple-500/20">
              <CardHeader>
                <CardTitle className="text-2xl text-white">Configure Predictions</CardTitle>
                <CardDescription className="text-purple-200">
                  Customize player, game details, and betting parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="playerName" className="text-white">Player Name</Label>
                    <Input
                      id="playerName"
                      value={playerName}
                      onChange={(e) => setPlayerName(e.target.value)}
                      className="bg-slate-700 border-gray-600 text-white"
                      placeholder="LeBron James"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gameDate" className="text-white">Game Date</Label>
                    <Input
                      id="gameDate"
                      type="date"
                      value={gameDate}
                      onChange={(e) => setGameDate(e.target.value)}
                      className="bg-slate-700 border-gray-600 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="team" className="text-white">Team</Label>
                    <Input
                      id="team"
                      value={team}
                      onChange={(e) => setTeam(e.target.value)}
                      className="bg-slate-700 border-gray-600 text-white"
                      placeholder="LAL"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="opponent" className="text-white">Opponent</Label>
                    <Input
                      id="opponent"
                      value={opponent}
                      onChange={(e) => setOpponent(e.target.value)}
                      className="bg-slate-700 border-gray-600 text-white"
                      placeholder="GSW"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bankroll" className="text-white">Bankroll ($)</Label>
                    <Input
                      id="bankroll"
                      type="number"
                      value={bankroll}
                      onChange={(e) => setBankroll(Number(e.target.value))}
                      className="bg-slate-700 border-gray-600 text-white"
                      placeholder="10000"
                    />
                  </div>
                </div>
                <Button 
                  onClick={fetchPredictions} 
                  className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  size="lg"
                >
                  <RefreshCw className="mr-2 h-5 w-5" />
                  Update Predictions
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
