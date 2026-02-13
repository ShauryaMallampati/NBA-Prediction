'use client'

import { Brain, TrendingUp, TrendingDown } from 'lucide-react'

interface FeatureExplanation {
  feature: string
  impact: 'positive' | 'negative'
  contribution: string
}

interface ExplainabilityCardProps {
  gameId: string
  homeTeam: string
  awayTeam: string
  topFeatures: FeatureExplanation[]
  summary: string
}

export function ExplainabilityCard({
  gameId,
  homeTeam,
  awayTeam,
  topFeatures,
  summary,
}: ExplainabilityCardProps) {
  return (
    <div className="bento-item">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center">
          <Brain className="w-5 h-5 text-muted-foreground" />
        </div>
        <div>
          <h3 className="font-semibold">Why this prediction?</h3>
          <p className="text-sm text-muted-foreground">{homeTeam} vs {awayTeam}</p>
        </div>
      </div>

      <div className="space-y-3 mb-4">
        {topFeatures.map((feature, index) => (
          <div
            key={`${gameId}-${index}`}
            className={`flex items-center justify-between p-3 rounded-md border ${feature.impact === 'positive'
              ? 'bg-success/10 border-success/20'
              : 'bg-destructive/10 border-destructive/20'
            }`}
          >
            <div className="flex items-center gap-2">
              {feature.impact === 'positive' ? (
                <TrendingUp className="w-4 h-4 text-success" />
              ) : (
                <TrendingDown className="w-4 h-4 text-destructive" />
              )}
              <span className="font-medium text-sm">
                {feature.feature.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())}
              </span>
            </div>
            <span className="font-semibold text-sm">
              {feature.contribution}
            </span>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-md bg-muted/40 border border-border">
        <p className="text-sm text-muted-foreground leading-relaxed">{summary}</p>
      </div>
    </div>
  )
}
