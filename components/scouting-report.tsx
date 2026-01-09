"use client"

import { FileText, ChevronDown, ChevronUp, CheckCircle, AlertTriangle } from "lucide-react"
import { useState } from "react"

interface ScoutingReportProps {
    gameId: string
    homeTeam: string
    awayTeam: string
    report: string
    prediction?: string
    confidence?: number
}

export function ScoutingReport({
    gameId,
    homeTeam,
    awayTeam,
    report,
    prediction = "HOME_WIN",
    confidence = 65
}: ScoutingReportProps) {
    const [expanded, setExpanded] = useState(false)

    // Parse markdown-like report into sections
    const renderReport = (text: string) => {
        const lines = text.split('\n')
        return lines.map((line, i) => {
            if (line.startsWith('## ')) {
                return <h2 key={i} className="text-xl font-bold text-white mt-4 mb-2">{line.replace('## ', '').replace('🏀 ', '')}</h2>
            }
            if (line.startsWith('### ')) {
                return <h3 key={i} className="text-lg font-semibold text-purple-300 mt-3 mb-2">{line.replace('### ', '')}</h3>
            }
            if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="font-bold text-green-400 my-2">{line.replace(/\*\*/g, '')}</p>
            }
            if (line.startsWith('- ')) {
                const isPositive = line.includes('+')
                return (
                    <div key={i} className={`flex items-center gap-2 py-1 px-3 rounded-lg my-1 ${isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                        {isPositive ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                        <span className="text-sm">{line.replace('- ', '')}</span>
                    </div>
                )
            }
            if (line.startsWith('*Generated')) {
                return <p key={i} className="text-xs text-muted-foreground mt-4 italic">{line.replace(/\*/g, '')}</p>
            }
            if (line.trim() === '---') {
                return <hr key={i} className="border-border my-3" />
            }
            if (line.trim()) {
                return <p key={i} className="text-gray-300 my-1">{line}</p>
            }
            return null
        })
    }

    return (
        <div className="rounded-2xl glass-strong border-2 border-blue-500/30 hover:border-blue-400/50 transition-all overflow-hidden">
            <div
                className="flex items-center justify-between cursor-pointer p-6"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                        <FileText className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg">AI Scouting Report</h3>
                        <p className="text-sm text-muted-foreground">{homeTeam} vs {awayTeam}</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className={`px-3 py-1 rounded-lg text-sm font-bold ${confidence >= 70
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                            : confidence >= 50
                                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                        }`}>
                        {confidence}% Conf
                    </div>
                    <button className="p-2 rounded-lg hover:bg-accent transition-colors">
                        {expanded ? (
                            <ChevronUp className="w-5 h-5" />
                        ) : (
                            <ChevronDown className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>

            {expanded && (
                <div className="px-6 pb-6 pt-2 border-t border-border bg-gradient-to-b from-transparent to-blue-500/5">
                    {renderReport(report)}
                </div>
            )}
        </div>
    )
}
