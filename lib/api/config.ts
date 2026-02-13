// Environment-aware API configuration
// On Vercel, use relative paths to hit Next.js API routes
// Locally, can use FastAPI backend if NEXT_PUBLIC_API_URL is set
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

export const API_ENDPOINTS = {
    predictions: '/predictions',
    prediction: (gameId: string) => `/predictions/${gameId}`,
    schedule: '/schedule',
    modelInfo: '/model/info',
    health: '/health',
    accuracy: '/accuracy',
    analysis: '/analysis',
    chemistryLeague: '/chemistry/league',
    chemistryMatchup: (home: string, away: string) => `/chemistry/matchup/${home}/${away}`,
    explain: (gameId: string) => `/explain/${gameId}`,
    scoutingReport: (gameId: string) => `/scouting-report/${gameId}`,
    teamCompare: (teamA: string, teamB: string) => `/teams/compare?teamA=${teamA}&teamB=${teamB}`,
} as const
