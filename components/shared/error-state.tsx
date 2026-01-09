'use client'

import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorStateProps {
    title?: string
    message: string
    retry?: () => void
}

export function ErrorState({ title = 'Something went wrong', message, retry }: ErrorStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-4">
                <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-muted-foreground max-w-md">{message}</p>
            {retry && (
                <button
                    onClick={retry}
                    className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                </button>
            )}
            <p className="mt-6 text-xs text-muted-foreground">
                Make sure the API is running:{' '}
                <code className="px-2 py-1 rounded bg-muted">
                    poetry run python src/api/ensemble_predictions.py
                </code>
            </p>
        </div>
    )
}
