'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    BarChart3,
    Brain,
    Calendar,
    FlaskConical,
    Home,
    Settings,
    Target,
    Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Predictions', href: '/predictions', icon: Target },
    { name: 'Schedule', href: '/schedule', icon: Calendar },
    { name: 'Teams', href: '/teams', icon: Users },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Chemistry', href: '/chemistry', icon: FlaskConical },
    { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
            <div className="flex min-h-0 flex-1 flex-col border-r border-border bg-card">
                {/* Logo */}
                <div className="flex h-16 shrink-0 items-center gap-3 px-6 border-b border-border">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xl">
                        🏀
                    </div>
                    <div>
                        <h1 className="text-lg font-bold">NBA Intel</h1>
                        <p className="text-xs text-muted-foreground">ML Analytics</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 px-3 py-4">
                    {navigation.map((item) => {
                        const isActive = pathname === item.href
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={cn(
                                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                                    isActive
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                )}
                            >
                                <item.icon className={cn('h-5 w-5', isActive && 'text-primary')} />
                                {item.name}
                                {isActive && (
                                    <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* Footer */}
                <div className="border-t border-border p-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        <span>API Connected</span>
                    </div>
                </div>
            </div>
        </aside>
    )
}
