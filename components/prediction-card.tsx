'use client'

import { motion } from 'framer-motion'
import { ConfidenceMeter } from '@/components/confidence-meter'
import { TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'

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

  const getConfidenceLevel = (conf: number) => {
    if (conf >= 0.7) return { label: 'High', color: 'text-success' }
    if (conf >= 0.5) return { label: 'Medium', color: 'text-secondary' }
    return { label: 'Low', color: 'text-muted-foreground' }
  }

  const confidenceLevel = getConfidenceLevel(displayConfidence)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn('w-full', className)}
    >
      <div className="bento-item">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Prediction</span>
            {date && <span className="text-xs text-muted-foreground">{date}</span>}
          </div>
          <span className={cn('text-xs font-medium', confidenceLevel.color)}>
            {confidenceLevel.label} Confidence
          </span>
        </div>

        <div className="space-y-4">
          <TeamRow
            label="Home"
            team={homeTeam}
            percentage={homePercentage}
            highlight={homeWinProb > awayWinProb}
          />
          <ConfidenceMeter confidence={homeWinProb} size="lg" showLabel={false} />
          <TeamRow
            label="Away"
            team={awayTeam}
            percentage={awayPercentage}
            highlight={awayWinProb > homeWinProb}
          />
          <ConfidenceMeter confidence={awayWinProb} size="lg" showLabel={false} />
        </div>

        <div className="my-4 divider" />

        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Predicted winner</span>
            <span className="font-medium">{predictedWinner}</span>
          </div>
          {expectedScore && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Expected score</span>
              <span className="font-medium">{expectedScore}</span>
            </div>
          )}
          {vegasLine && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Vegas line</span>
              <span className="font-medium">{vegasLine}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Confidence</span>
            <ConfidenceMeter confidence={displayConfidence} size="sm" />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function TeamRow({
  label,
  team,
  percentage,
  highlight,
}: {
  label: string
  team: string
  percentage: number
  highlight: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs font-semibold">
          {team.slice(0, 3).toUpperCase()}
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
          <span className="font-semibold">{team}</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="text-2xl font-bold tabular-nums">{percentage}%</div>
          <div className="text-xs text-muted-foreground">Win probability</div>
        </div>
        {highlight && <TrendingUp className="w-5 h-5 text-success" />}
      </div>
    </div>
  )
}
