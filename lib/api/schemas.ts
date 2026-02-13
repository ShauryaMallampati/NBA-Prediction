import { z } from 'zod'

// Game Prediction Schema
export const GamePredictionSchema = z.object({
    game_id: z.string(),
    home_team: z.string(),
    away_team: z.string(),
    commence_time: z.string(),
    prediction: z.enum(['HOME_WIN', 'AWAY_WIN']),
    home_win_probability: z.number(),
    away_win_probability: z.number(),
    confidence: z.number(),
    models_agree: z.union([z.number(), z.string()]).optional(),
    consensus_percentage: z.number().optional(),
    individual_votes: z.record(z.string(), z.string()).optional(),
    home_odds: z.number().optional(),
    away_odds: z.number().optional(),
    home_spread: z.number().optional(),
    away_spread: z.number().optional(),
})

export const PredictionsResponseSchema = z.object({
    timestamp: z.string().optional(),
    total_games: z.number().optional(),
    predictions: z.array(GamePredictionSchema).default([]),
    message: z.string().optional(),
    model_info: z.object({
        num_models: z.number(),
        model_names: z.array(z.string()),
        num_features: z.number(),
        feature_names: z.array(z.string()).optional(),
    }).optional(),
}).passthrough()

// Schedule Schema
export const ScheduleGameSchema = z.object({
    game_id: z.string(),
    date: z.string(),
    home_team: z.string(),
    away_team: z.string(),
    game_time: z.string().optional(),
})

export const ScheduleResponseSchema = z.object({
    success: z.boolean(),
    source: z.string().optional(),
    count: z.number(),
    games: z.array(ScheduleGameSchema),
    message: z.string().optional(),
}).passthrough()

// Chemistry Schema
export const DuoSchema = z.object({
    players: z.string(),
    team: z.string(),
    net_rating: z.number(),
    games: z.number(),
    chemistry_score: z.number().optional(),
})

export const TeamRankingSchema = z.object({
    team: z.string(),
    chemistry_score: z.number(),
})

export const ChemistryLeagueResponseSchema = z.object({
    total_teams: z.number(),
    total_pairs: z.number(),
    top_duos: z.array(DuoSchema),
    team_rankings: z.array(TeamRankingSchema),
}).passthrough()

// Model Info Schema
export const ModelInfoResponseSchema = z.object({
    is_trained: z.boolean(),
    num_models: z.number(),
    model_names: z.array(z.string()),
    feature_count: z.number(),
    feature_names: z.array(z.string()),
    training_history: z.array(z.record(z.any())).optional(),
    last_training: z.record(z.any()).nullable().optional(),
    world_model_status: z.object({
        rnn_active: z.boolean(),
        cnn_active: z.boolean(),
    }).optional(),
}).passthrough()

// Health Schema
export const HealthResponseSchema = z.object({
    status: z.string(),
    model_loaded: z.boolean(),
    timestamp: z.string(),
}).passthrough()

// Explanation Schema
export const ExplanationResponseSchema = z.object({
    game_id: z.string(),
    explanation: z.object({
        top_features: z.array(z.object({
            feature: z.string(),
            impact: z.string(),
            contribution: z.string(),
        })),
        summary: z.string(),
        confidence_drivers: z.array(z.string()),
    }),
})

// Export types
export type GamePrediction = z.infer<typeof GamePredictionSchema>
export type PredictionsResponse = z.infer<typeof PredictionsResponseSchema>
export type ScheduleGame = z.infer<typeof ScheduleGameSchema>
export type ScheduleResponse = z.infer<typeof ScheduleResponseSchema>
export type ChemistryLeagueResponse = z.infer<typeof ChemistryLeagueResponseSchema>
export type ModelInfoResponse = z.infer<typeof ModelInfoResponseSchema>
export type HealthResponse = z.infer<typeof HealthResponseSchema>
export type ExplanationResponse = z.infer<typeof ExplanationResponseSchema>
