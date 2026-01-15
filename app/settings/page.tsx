'use client'

import { useTheme } from 'next-themes'
import { Moon, Settings2, Sun } from 'lucide-react'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()

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

