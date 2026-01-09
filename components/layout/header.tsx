'use client'

import { useTheme } from 'next-themes'
import { Moon, Sun, RefreshCw } from 'lucide-react'
import { useRefreshPredictions } from '@/lib/hooks'

interface HeaderProps {
    title: string
    description?: string
    showRefresh?: boolean
    isRefreshing?: boolean
}

export function Header({ title, description, showRefresh, isRefreshing }: HeaderProps) {
    const { theme, setTheme } = useTheme()
    const refreshPredictions = useRefreshPredictions()

    return (
        <header className="sticky top-0 lg:top-0 z-30 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-16 items-center justify-between px-6">
                <div>
                    <h1 className="text-xl font-bold">{title}</h1>
                    {description && (
                        <p className="text-sm text-muted-foreground">{description}</p>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {showRefresh && (
                        <button
                            onClick={() => refreshPredictions()}
                            className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-accent transition-colors"
                        >
                            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                            Refresh
                        </button>
                    )}
                    <button
                        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                        className="p-2 rounded-lg hover:bg-accent transition-colors"
                    >
                        {theme === 'dark' ? (
                            <Sun className="h-5 w-5" />
                        ) : (
                            <Moon className="h-5 w-5" />
                        )}
                    </button>
                </div>
            </div>
        </header>
    )
}
