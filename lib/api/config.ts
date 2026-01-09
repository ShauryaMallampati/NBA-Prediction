// Environment-aware API configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
    predictions: '/predictions',
    prediction: (gameId: string) => `/predictions/${gameId}`,
    schedule: '/live_schedule',
    modelInfo: '/model/info',
    health: '/health',
    chemistryLeague: '/chemistry/league',
    chemistryMatchup: (home: string, away: string) => `/chemistry/matchup/${home}/${away}`,
    explain: (gameId: string) => `/explain/${gameId}`,
    scoutingReport: (gameId: string) => `/scouting-report/${gameId}`,
} as const
