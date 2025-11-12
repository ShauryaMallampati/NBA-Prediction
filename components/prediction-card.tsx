"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { ConfidenceMeter } from "@/components/confidence-meter"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface PredictionCardProps {
  homeTeam: string
  awayTeam: string
  homeWinProb: number // 0-1
  awayWinProb: number // 0-1
  expectedScore?: string
  vegasLine?: string
  confidence?: number // 0-1
  date?: string
  className?: string
}

export function PredictionCard({
  homeTeam,
  awayTeam,
  homeWinProb,
  awayWinProb,
  expectedScore,
  vegasLine,
  confidence,
  date,
  className,
}: PredictionCardProps) {
  const homePercentage = Math.round(homeWinProb * 100)
  const awayPercentage = Math.round(awayWinProb * 100)
  const predictedWinner = homeWinProb > awayWinProb ? homeTeam : awayTeam
  const winMargin = Math.abs(homeWinProb - awayWinProb)
  const displayConfidence = confidence ?? winMargin * 2

  // Determine confidence level
  const getConfidenceLevel = (conf: number) => {
    if (conf >= 0.7) return { label: "High", color: "text-green-500" }
    if (conf >= 0.5) return { label: "Medium", color: "text-yellow-500" }
    return { label: "Low", color: "text-red-500" }
  }

  const confidenceLevel = getConfidenceLevel(displayConfidence)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("w-full", className)}
    >
      <Card className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Prediction</span>
            {date && <span className="text-xs text-gray-500">{date}</span>}
          </div>
          <span className={cn("text-xs font-medium", confidenceLevel.color)}>
            {confidenceLevel.label} Confidence
          </span>
        </div>

        {/* Teams */}
        <div className="space-y-4">
          {/* Home Team */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center text-white font-bold">
                {homeTeam.slice(0, 2)}
              </div>
              <span className="font-semibold text-white">{homeTeam}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-white">{homePercentage}%</div>
                <div className="text-xs text-gray-400">Win Probability</div>
              </div>
              {homeWinProb > awayWinProb && (
                <TrendingUp className="w-5 h-5 text-green-500" />
              )}
            </div>
          </div>

          {/* Confidence Meter */}
          <ConfidenceMeter confidence={homeWinProb} size="lg" showLabel={false} />

          {/* Away Team */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center text-white font-bold">
                {awayTeam.slice(0, 2)}
              </div>
              <span className="font-semibold text-white">{awayTeam}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-white">{awayPercentage}%</div>
                <div className="text-xs text-gray-400">Win Probability</div>
              </div>
              {awayWinProb > homeWinProb && (
                <TrendingUp className="w-5 h-5 text-green-500" />
              )}
            </div>
          </div>

          {/* Confidence Meter */}
          <ConfidenceMeter confidence={awayWinProb} size="lg" showLabel={false} />
        </div>

        {/* Divider */}
        <div className="my-4 border-t border-slate-700" />

        {/* Prediction Summary */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Predicted Winner</span>
            <span className="font-semibold text-white">{predictedWinner}</span>
          </div>
          {expectedScore && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Expected Score</span>
              <span className="text-sm text-white">{expectedScore}</span>
            </div>
          )}
          {vegasLine && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Vegas Line</span>
              <span className="text-sm text-white">{vegasLine}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Confidence</span>
            <ConfidenceMeter confidence={displayConfidence} size="sm" />
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

