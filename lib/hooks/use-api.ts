'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
    fetchPredictions,
    fetchSchedule,
    fetchChemistryLeague,
    fetchModelInfo,
    fetchHealth,
    fetchExplanation,
} from '@/lib/api'

// Query keys for cache management
export const queryKeys = {
    predictions: ['predictions'] as const,
    schedule: (days: number) => ['schedule', days] as const,
    chemistry: ['chemistry', 'league'] as const,
    modelInfo: ['model', 'info'] as const,
    health: ['health'] as const,
    explanation: (gameId: string) => ['explanation', gameId] as const,
}

// Predictions hook
export function usePredictions() {
    return useQuery({
        queryKey: queryKeys.predictions,
        queryFn: fetchPredictions,
        staleTime: 1000 * 60 * 2, // 2 minutes
        refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
    })
}

// Schedule hook
export function useSchedule(days: number = 14) {
    return useQuery({
        queryKey: queryKeys.schedule(days),
        queryFn: () => fetchSchedule(days),
        staleTime: 1000 * 60 * 10, // 10 minutes
    })
}

// Chemistry hook
export function useChemistry() {
    return useQuery({
        queryKey: queryKeys.chemistry,
        queryFn: fetchChemistryLeague,
        staleTime: 1000 * 60 * 30, // 30 minutes (rarely changes)
    })
}

// Model info hook
export function useModelInfo() {
    return useQuery({
        queryKey: queryKeys.modelInfo,
        queryFn: fetchModelInfo,
        staleTime: 1000 * 60 * 60, // 1 hour
    })
}

// Health check hook
export function useHealth() {
    return useQuery({
        queryKey: queryKeys.health,
        queryFn: fetchHealth,
        staleTime: 1000 * 30, // 30 seconds
        refetchInterval: 1000 * 60, // Check every minute
    })
}

// Explanation hook
export function useExplanation(gameId: string | null) {
    return useQuery({
        queryKey: queryKeys.explanation(gameId || ''),
        queryFn: () => fetchExplanation(gameId!),
        enabled: !!gameId,
        staleTime: 1000 * 60 * 5,
    })
}

// Hook to invalidate and refetch predictions
export function useRefreshPredictions() {
    const queryClient = useQueryClient()

    return () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.predictions })
    }
}

// Accuracy hook - fetches dynamic model accuracy
export function useAccuracy() {
    return useQuery({
        queryKey: ['accuracy'] as const,
        queryFn: async () => {
            const response = await fetch('/api/accuracy')
            if (!response.ok) {
                throw new Error('Accuracy data unavailable')
            }
            const data = await response.json() as {
                success: boolean
                accuracy: number | null
                total_games: number
                total_correct: number
                days_evaluated: number
                source: string
                message?: string
            }
            if (!data.success) {
                throw new Error(data.message || 'Accuracy data unavailable')
            }
            return data
        },
        staleTime: 1000 * 60 * 10, // 10 minutes
        retry: 1,
    })
}
