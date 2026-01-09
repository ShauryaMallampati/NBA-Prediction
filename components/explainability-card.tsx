"use client"

import { Brain, TrendingUp, TrendingDown } from "lucide-react"

interface FeatureExplanation {
    feature: string
    impact: "positive" | "negative"
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
    summary
}: ExplainabilityCardProps) {
    return (
        <div className="p-6 rounded-2xl glass-strong border-2 border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h3 className="font-bold text-lg">Why This Prediction?</h3>
                    <p className="text-sm text-muted-foreground">{homeTeam} vs {awayTeam}</p>
                </div>
            </div>

            <div className="space-y-3 mb-4">
                {topFeatures.map((f, i) => (
                    <div
                        key={i}
                        className={`flex items-center justify-between p-3 rounded-lg border ${f.impact === "positive"
                                ? "bg-green-500/10 border-green-500/30"
                                : "bg-red-500/10 border-red-500/30"
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            {f.impact === "positive" ? (
                                <TrendingUp className="w-4 h-4 text-green-400" />
                            ) : (
                                <TrendingDown className="w-4 h-4 text-red-400" />
                            )}
                            <span className="font-medium text-sm">
                                {f.feature.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                        </div>
                        <span className={`font-bold text-sm ${f.impact === "positive" ? "text-green-400" : "text-red-400"
                            }`}>
                            {f.contribution}
                        </span>
                    </div>
                ))}
            </div>

            <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                <p className="text-sm text-purple-200 leading-relaxed">{summary}</p>
            </div>
        </div>
    )
}
