import { API_BASE_URL, API_ENDPOINTS } from './config'
import {
    PredictionsResponseSchema,
    ScheduleResponseSchema,
    ChemistryLeagueResponseSchema,
    ModelInfoResponseSchema,
    HealthResponseSchema,
    ExplanationResponseSchema,
    GamePredictionSchema,
    type PredictionsResponse,
    type ScheduleResponse,
    type ChemistryLeagueResponse,
    type ModelInfoResponse,
    type HealthResponse,
    type ExplanationResponse,
    type GamePrediction,
} from './schemas'

class APIError extends Error {
    constructor(public status: number, message: string) {
        super(message)
        this.name = 'APIError'
    }
}

async function fetchAPI<T>(
    endpoint: string,
    schema: { parse: (data: unknown) => T },
    options?: RequestInit
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    })

    if (!response.ok) {
        throw new APIError(response.status, `API Error: ${response.statusText}`)
    }

    const data = await response.json()

    // Validate response with Zod schema
    try {
        return schema.parse(data)
    } catch (e) {
        console.error('API Response validation failed:', e)
        // Return data anyway for graceful degradation
        return data as T
    }
}

// API Functions
export async function fetchPredictions(): Promise<PredictionsResponse> {
    return fetchAPI(API_ENDPOINTS.predictions, PredictionsResponseSchema)
}

export async function fetchPrediction(gameId: string): Promise<GamePrediction> {
    return fetchAPI(API_ENDPOINTS.prediction(gameId), GamePredictionSchema)
}

export async function fetchSchedule(days: number = 14): Promise<ScheduleResponse> {
    return fetchAPI(`${API_ENDPOINTS.schedule}?days=${days}`, ScheduleResponseSchema)
}

export async function fetchChemistryLeague(): Promise<ChemistryLeagueResponse> {
    return fetchAPI(API_ENDPOINTS.chemistryLeague, ChemistryLeagueResponseSchema)
}

export async function fetchModelInfo(): Promise<ModelInfoResponse> {
    return fetchAPI(API_ENDPOINTS.modelInfo, ModelInfoResponseSchema)
}

export async function fetchHealth(): Promise<HealthResponse> {
    return fetchAPI(API_ENDPOINTS.health, HealthResponseSchema)
}

export async function fetchExplanation(gameId: string): Promise<ExplanationResponse> {
    return fetchAPI(API_ENDPOINTS.explain(gameId), ExplanationResponseSchema)
}

export { APIError }
