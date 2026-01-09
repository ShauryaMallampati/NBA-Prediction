// Date/Time formatters
export function formatGameTime(isoString: string): string {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
    })
}

export function formatShortDate(isoString: string): string {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    })
}

export function formatTime(isoString: string): string {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
    })
}

// Number formatters
export function formatPercent(value: number, decimals: number = 0): string {
    return `${value.toFixed(decimals)}%`
}

export function formatOdds(odds: number): string {
    if (odds > 0) return `+${odds}`
    return odds.toString()
}

export function formatSpread(spread: number): string {
    if (spread > 0) return `+${spread.toFixed(1)}`
    return spread.toFixed(1)
}

// Color utilities
// Color utilities
export function getConfidenceColor(confidence: number): string {
    if (confidence >= 65) return 'text-green-400'
    if (confidence >= 58) return 'text-yellow-400'
    return 'text-orange-400'
}

export function getConfidenceBg(confidence: number): string {
    if (confidence >= 65) return 'bg-green-500/20 border-green-500/30'
    if (confidence >= 58) return 'bg-yellow-500/20 border-yellow-500/30'
    return 'bg-orange-500/20 border-orange-500/30'
}

export function getProbabilityColor(isWinner: boolean): string {
    return isWinner ? 'text-green-400' : 'text-muted-foreground'
}
