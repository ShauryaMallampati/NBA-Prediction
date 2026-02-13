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
            <div className="w-12 h-12 rounded-md bg-destructive/10 flex items-center justify-center mb-4">
                <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-muted-foreground max-w-md">{message}</p>
            {retry && (
                <button
                    onClick={retry}
                    className="btn-primary mt-4"
                >
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                </button>
            )}
            <p className="mt-6 text-xs text-muted-foreground">
                If you rely on the FastAPI backend, make sure it is running and your
                <span className="font-mono"> NEXT_PUBLIC_API_URL</span> is set.
            </p>
        </div>
    )
}
