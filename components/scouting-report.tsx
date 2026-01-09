"use client"

import { FileText, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"

interface ScoutingReportProps {
    gameId: string
    homeTeam: string
    awayTeam: string
    report: string
}

export function ScoutingReport({ gameId, homeTeam, awayTeam, report }: ScoutingReportProps) {
    const [expanded, setExpanded] = useState(false)

    return (
        <div className="p-6 rounded-2xl glass-strong border-2 border-blue-500/30 hover:border-blue-400/50 transition-all">
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg">AI Scouting Report</h3>
                        <p className="text-sm text-muted-foreground">{homeTeam} vs {awayTeam}</p>
                    </div>
                </div>
                <button className="p-2 rounded-lg hover:bg-accent transition-colors">
                    {expanded ? (
                        <ChevronUp className="w-5 h-5" />
                    ) : (
                        <ChevronDown className="w-5 h-5" />
                    )}
                </button>
            </div>

            {expanded && (
                <div className="mt-4 pt-4 border-t border-border">
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{report}</ReactMarkdown>
                    </div>
                </div>
            )}
        </div>
    )
}
