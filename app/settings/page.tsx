'use client'

import { useTheme } from 'next-themes'
import { Header } from '@/components/layout/header'
import { useHealth } from '@/lib/hooks'
import { API_BASE_URL } from '@/lib/api/config'
import { CheckCircle, ExternalLink, Github, Moon, Settings2, Sun, XCircle } from 'lucide-react'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const { data: health, isLoading } = useHealth()

    return (
        <div className="min-h-screen">
            <Header
                title="Settings"
                description="Application configuration and status"
            />

            <div className="container mx-auto px-6 py-8 max-w-3xl">
                {/* API Status */}
                <div className="rounded-xl border border-border bg-card p-6 mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Settings2 className="h-5 w-5 text-primary" />
                        <h2 className="text-lg font-bold">API Status</h2>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                            <div>
                                <div className="font-medium">Backend API</div>
                                <div className="text-sm text-muted-foreground">{API_BASE_URL}</div>
                            </div>
                            {isLoading ? (
                                <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                            ) : health ? (
                                <div className="flex items-center gap-2 text-green-400">
                                    <CheckCircle className="h-5 w-5" />
                                    <span className="font-medium">Connected</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-red-400">
                                    <XCircle className="h-5 w-5" />
                                    <span className="font-medium">Disconnected</span>
                                </div>
                            )}
                        </div>

                        {health && (
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div className="p-3 rounded-lg bg-muted/30">
                                    <div className="text-muted-foreground">Model Loaded</div>
                                    <div className={`font-medium ${health.model_loaded ? 'text-green-400' : 'text-red-400'}`}>
                                        {health.model_loaded ? 'Yes' : 'No'}
                                    </div>
                                </div>
                                <div className="p-3 rounded-lg bg-muted/30">
                                    <div className="text-muted-foreground">Last Check</div>
                                    <div className="font-medium">
                                        {new Date(health.timestamp).toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Theme */}
                <div className="rounded-xl border border-border bg-card p-6 mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        {theme === 'dark' ? <Moon className="h-5 w-5 text-primary" /> : <Sun className="h-5 w-5 text-primary" />}
                        <h2 className="text-lg font-bold">Appearance</h2>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={() => setTheme('light')}
                            className={`flex-1 p-4 rounded-lg border transition-colors ${theme === 'light'
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:bg-accent'
                                }`}
                        >
                            <Sun className="h-6 w-6 mx-auto mb-2" />
                            <div className="text-sm font-medium text-center">Light</div>
                        </button>
                        <button
                            onClick={() => setTheme('dark')}
                            className={`flex-1 p-4 rounded-lg border transition-colors ${theme === 'dark'
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:bg-accent'
                                }`}
                        >
                            <Moon className="h-6 w-6 mx-auto mb-2" />
                            <div className="text-sm font-medium text-center">Dark</div>
                        </button>
                        <button
                            onClick={() => setTheme('system')}
                            className={`flex-1 p-4 rounded-lg border transition-colors ${theme === 'system'
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:bg-accent'
                                }`}
                        >
                            <Settings2 className="h-6 w-6 mx-auto mb-2" />
                            <div className="text-sm font-medium text-center">System</div>
                        </button>
                    </div>
                </div>

                {/* About */}
                <div className="rounded-xl border border-border bg-card p-6">
                    <h2 className="text-lg font-bold mb-4">About</h2>

                    <div className="space-y-4 text-sm">
                        <div className="flex justify-between p-3 rounded-lg bg-muted/30">
                            <span className="text-muted-foreground">Version</span>
                            <span className="font-medium">2.0.0</span>
                        </div>
                        <div className="flex justify-between p-3 rounded-lg bg-muted/30">
                            <span className="text-muted-foreground">Framework</span>
                            <span className="font-medium">Next.js 14 + TanStack Query</span>
                        </div>
                        <div className="flex justify-between p-3 rounded-lg bg-muted/30">
                            <span className="text-muted-foreground">ML Stack</span>
                            <span className="font-medium">XGBoost + LightGBM + CatBoost</span>
                        </div>
                    </div>

                    <a
                        href="https://github.com/ShauryaMallampati/NBA-Prediciton"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 mt-6 p-3 rounded-lg border border-border hover:bg-accent transition-colors"
                    >
                        <Github className="h-5 w-5" />
                        <span>View on GitHub</span>
                        <ExternalLink className="h-4 w-4" />
                    </a>
                </div>
            </div>
        </div>
    )
}
