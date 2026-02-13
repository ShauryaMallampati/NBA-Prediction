'use client'

import { useTheme } from 'next-themes'
import { Moon, Settings2, Sun } from 'lucide-react'
import { useHealth, useModelInfo } from '@/lib/hooks'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const { data: health } = useHealth()
    const { data: modelInfo } = useModelInfo()

    return (
        <div className="min-h-screen">
            {/* Page Header */}
            <header className="border-b border-border">
                <div className="container-wide py-8">
                    <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
                    <p className="text-muted-foreground">Application preferences</p>
                </div>
            </header>

            <div className="container-wide py-8 max-w-3xl">
                {/* Theme */}
                <section className="bento-item">
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

                <section className="bento-item mt-6">
                    <h2 className="font-semibold mb-4">System status</h2>
                    <div className="grid md:grid-cols-3 gap-4">
                        <StatusPill label="API" value={health?.status ?? '—'} />
                        <StatusPill label="Model loaded" value={health ? (health.model_loaded ? 'Yes' : 'No') : '—'} />
                        <StatusPill label="Models" value={modelInfo?.num_models ?? '—'} />
                    </div>
                    {modelInfo?.last_training && (
                        <p className="mt-3 text-xs text-muted-foreground">
                            Last trained: {typeof modelInfo.last_training === 'string'
                                ? modelInfo.last_training
                                : JSON.stringify(modelInfo.last_training)}
                        </p>
                    )}
                </section>
            </div>
        </div>
    )
}

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

function StatusPill({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-md border border-border p-3">
            <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
            <div className="text-lg font-semibold">{value}</div>
        </div>
    )
}
