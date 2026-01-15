'use client'

import { useTheme } from 'next-themes'
import { useHealth } from '@/lib/hooks'
import { API_BASE_URL } from '@/lib/api/config'
import { CheckCircle, ExternalLink, Github, Moon, Settings2, Sun, XCircle } from 'lucide-react'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const { data: health, isLoading } = useHealth()

    return (
        <div className="min-h-screen">
            {/* Page Header */}
            <header className="border-b border-border">
                <div className="container-wide py-8">
                    <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
                    <p className="text-muted-foreground">Application configuration and status</p>
                </div>
            </header>

            <div className="container-wide py-8 max-w-3xl">
                {/* API Status */}
                <section className="bento-item mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Settings2 className="h-5 w-5 text-muted-foreground" />
                        <h2 className="font-semibold">API Status</h2>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-md bg-muted/30">
                            <div>
                                <div className="font-medium">Backend API</div>
                                <div className="text-sm text-muted-foreground font-mono">{API_BASE_URL}</div>
                            </div>
                            {isLoading ? (
                                <div className="w-5 h-5 rounded-full border-2 border-foreground border-t-transparent animate-spin" />
                            ) : health ? (
                                <div className="flex items-center gap-2 text-success">
                                    <CheckCircle className="h-5 w-5" />
                                    <span className="font-medium">Connected</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-destructive">
                                    <XCircle className="h-5 w-5" />
                                    <span className="font-medium">Disconnected</span>
                                </div>
                            )}
                        </div>

                        {health && (
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div className="p-3 rounded-md bg-muted/30">
                                    <div className="text-muted-foreground">Model Loaded</div>
                                    <div className={`font-medium ${health.model_loaded ? 'text-success' : 'text-destructive'}`}>
                                        {health.model_loaded ? 'Yes' : 'No'}
                                    </div>
                                </div>
                                <div className="p-3 rounded-md bg-muted/30">
                                    <div className="text-muted-foreground">Last Check</div>
                                    <div className="font-mono">
                                        {new Date(health.timestamp).toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </section>

                {/* Theme */}
                <section className="bento-item mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        {theme === 'dark' ? <Moon className="h-5 w-5 text-muted-foreground" /> : <Sun className="h-5 w-5 text-muted-foreground" />}
                        <h2 className="font-semibold">Appearance</h2>
                    </div>

                    <div className="flex gap-3">
                        <ThemeButton
                            label="Light"
                            icon={Sun}
                            isActive={theme === 'light'}
                            onClick={() => setTheme('light')}
                        />
                        <ThemeButton
                            label="Dark"
                            icon={Moon}
                            isActive={theme === 'dark'}
                            onClick={() => setTheme('dark')}
                        />
                        <ThemeButton
                            label="System"
                            icon={Settings2}
                            isActive={theme === 'system'}
                            onClick={() => setTheme('system')}
                        />
                    </div>
                </section>



                {/* About */}
                <section className="bento-item">
                    <h2 className="font-semibold mb-4">About</h2>

                    <div className="space-y-2 text-sm">
                        <InfoRow label="Version" value="2.0.0" />
                        <InfoRow label="Framework" value="Next.js 16 + TanStack Query" />
                        <InfoRow label="ML Stack" value="XGBoost + LightGBM + CatBoost" />
                    </div>

                    <a
                        href="https://github.com/ShauryaMallampati/NBA-Prediciton"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 mt-6 p-3 rounded-md border border-border hover:bg-accent transition-colors"
                    >
                        <Github className="h-5 w-5" />
                        <span>View on GitHub</span>
                        <ExternalLink className="h-4 w-4" />
                    </a>
                </section>
            </div>
        </div>
    )
}

// ==============================================
// COMPONENTS
// ==============================================

function ThemeButton({ label, icon: Icon, isActive, onClick }: {
    label: string
    icon: React.ElementType
    isActive: boolean
    onClick: () => void
}) {
    return (
        <button
            onClick={onClick}
            className={`flex-1 p-4 rounded-md border transition-colors ${isActive
                ? 'bg-foreground text-background border-foreground'
                : 'border-border hover:bg-accent'
                }`}
        >
            <Icon className="h-5 w-5 mx-auto mb-2" />
            <div className="text-sm font-medium text-center">{label}</div>
        </button>
    )
}

function InfoRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between p-3 rounded-md bg-muted/30">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium">{value}</span>
        </div>
    )
}
