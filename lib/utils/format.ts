// Date/Time formatters
export function formatGameTime(isoString: string): string {
    const date = new Date(isoString)
    if (Number.isNaN(date.getTime())) return '—'
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
    if (Number.isNaN(date.getTime())) return '—'
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    })
}

export function formatTime(isoString: string): string {
    const date = new Date(isoString)
    if (Number.isNaN(date.getTime())) return '—'
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

export function formatOdds(odds?: number): string {
    if (typeof odds !== 'number') return '—'
    if (odds > 0) return `+${odds}`
    return odds.toString()
}

export function formatSpread(spread?: number): string {
    if (typeof spread !== 'number') return '—'
    if (spread > 0) return `+${spread.toFixed(1)}`
    return spread.toFixed(1)
}

// Color utilities
// Color utilities
export function getConfidenceColor(confidence: number): string {
    if (confidence >= 65) return 'text-success'
    if (confidence >= 58) return 'text-secondary'
    return 'text-muted-foreground'
}

export function getConfidenceBg(confidence: number): string {
    if (confidence >= 65) return 'bg-success/10 border-success/20'
    if (confidence >= 58) return 'bg-secondary/10 border-secondary/20'
    return 'bg-muted border-border'
}

export function getProbabilityColor(isWinner: boolean): string {
    return isWinner ? 'text-green-400' : 'text-muted-foreground'
}
