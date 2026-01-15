'use client'

import { useState, useEffect } from 'react'
import { API_BASE_URL } from '@/lib/api/config'
import { PageSkeleton } from '@/components/shared/loading-skeleton'
import { AlertTriangle, Brain, Calendar, ChevronLeft, ChevronRight } from 'lucide-react'

interface Analysis {
    game_id: string
    home_team: string
    away_team: string
    prediction: string
    actual_winner: string
    home_score?: number
    away_score?: number
    confidence: number
    analysis: string
    analyzed_at: string
}

interface AnalysisResponse {
    success: boolean
    date: string
    count: number
    analyses: Analysis[]
    message?: string
}

export default function AnalysisPage() {
    const [data, setData] = useState<AnalysisResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedDate, setSelectedDate] = useState<string>(() => {
        const yesterday = new Date()
        yesterday.setDate(yesterday.getDate() - 1)
        return yesterday.toISOString().split('T')[0]
    })

    useEffect(() => {
        const fetchAnalysis = async () => {
            setIsLoading(true)
            setError(null)
            try {
                const res = await fetch(`${API_BASE_URL}/analysis?date=${selectedDate}`)
                if (!res.ok) throw new Error('Failed to fetch analysis')
                const json = await res.json()
                setData(json)
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Unknown error')
            } finally {
                setIsLoading(false)
            }
        }
        fetchAnalysis()
    }, [selectedDate])

    const handlePrevDay = () => {
        const date = new Date(selectedDate)
        date.setDate(date.getDate() - 1)
        setSelectedDate(date.toISOString().split('T')[0])
    }

    const handleNextDay = () => {
        const date = new Date(selectedDate)
        date.setDate(date.getDate() + 1)
        const today = new Date()
        if (date <= today) {
            setSelectedDate(date.toISOString().split('T')[0])
        }
    }

    return (
        <div className="min-h-screen">
            {/* Page Header */}
            <header className="border-b border-border">
                <div className="container-wide py-8">
                    <div className="flex items-center gap-3 mb-2">
                        <Brain className="h-6 w-6 text-muted-foreground" />
                        <h1 className="text-2xl font-bold tracking-tight">Why I Was Wrong</h1>
                    </div>
                    <p className="text-muted-foreground">
                        AI analysis of incorrect predictions using Qwen2.5-3B reasoning
                    </p>
                </div>
            </header>

            <div className="container-wide py-8">
                {/* Date Selector */}
                <div className="flex items-center justify-between mb-6">
                    <button
                        onClick={handlePrevDay}
                        className="p-2 rounded-md border border-border hover:bg-accent transition-colors"
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </button>

                    <div className="flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-muted-foreground" />
                        <span className="font-medium">{selectedDate}</span>
                    </div>

                    <button
                        onClick={handleNextDay}
                        className="p-2 rounded-md border border-border hover:bg-accent transition-colors"
                    >
                        <ChevronRight className="h-5 w-5" />
                    </button>
                </div>

                {isLoading && <PageSkeleton />}

                {error && (
                    <div className="bento-item text-center py-12">
                        <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-destructive">{error}</p>
                    </div>
                )}

                {!isLoading && !error && data?.analyses.length === 0 && (
                    <div className="bento-item text-center py-12">
                        <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No Wrong Predictions</h3>
                        <p className="text-sm text-muted-foreground">
                            {data.message || `No wrong predictions to analyze for ${selectedDate}`}
                        </p>
                    </div>
                )}

                {!isLoading && !error && data && data.analyses.length > 0 && (
                    <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            {data.count} incorrect prediction{data.count !== 1 ? 's' : ''} analyzed
                        </p>

                        {data.analyses.map((item, idx) => (
                            <div key={item.game_id || idx} className="bento-item">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="text-lg font-bold">
                                            {item.away_team} @ {item.home_team}
                                        </div>
                                        {item.away_score && item.home_score && (
                                            <div className="text-sm text-muted-foreground">
                                                {item.away_score} - {item.home_score}
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-sm font-mono text-muted-foreground">
                                        {item.confidence}% confident
                                    </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4 mb-4">
                                    <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
                                        <div className="text-xs text-muted-foreground mb-1">We Predicted</div>
                                        <div className="font-semibold text-destructive">{item.prediction}</div>
                                    </div>
                                    <div className="p-3 rounded-md bg-success/10 border border-success/20">
                                        <div className="text-xs text-muted-foreground mb-1">Actual Winner</div>
                                        <div className="font-semibold text-success">{item.actual_winner}</div>
                                    </div>
                                </div>

                                <div className="p-4 rounded-md bg-muted/30 border border-border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Brain className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-sm font-medium">AI Analysis</span>
                                    </div>
                                    <p className="text-sm leading-relaxed">{item.analysis}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
