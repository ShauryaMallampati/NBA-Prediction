'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
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
    { name: 'Analysis', href: '/analysis', icon: Brain },
    { name: 'Chemistry', href: '/chemistry', icon: FlaskConical },
]

const secondary = [
    { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
            <div className="flex min-h-0 flex-1 flex-col border-r border-border bg-card">
                {/* Logo - Clean, no gradients */}
                <div className="flex h-16 shrink-0 items-center gap-3 px-6 border-b border-border">
                    <div className="w-9 h-9 rounded-lg bg-foreground flex items-center justify-center">
                        <span className="text-background font-bold text-sm">NBA</span>
                    </div>
                    <div>
                        <h1 className="text-base font-semibold tracking-tight">NBA Intel</h1>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">ML Predictions</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4">
                    <div className="space-y-1">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={cn(
                                        'group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                                        isActive
                                            ? 'bg-foreground text-background'
                                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                    )}
                                >
                                    <item.icon className="h-4 w-4" />
                                    {item.name}
                                </Link>
                            )
                        })}
                    </div>

                    {/* Divider */}
                    <div className="my-4 h-px bg-border" />

                    {/* Secondary nav */}
                    <div className="space-y-1">
                        {secondary.map((item) => {
                            const isActive = pathname === item.href
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={cn(
                                        'group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                                        isActive
                                            ? 'bg-foreground text-background'
                                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                    )}
                                >
                                    <item.icon className="h-4 w-4" />
                                    {item.name}
                                </Link>
                            )
                        })}
                    </div>
                </nav>

                {/* Footer - Clean status */}
                <div className="border-t border-border p-4">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Status</span>
                        <div className="flex items-center gap-1.5">
                            <div className="h-1.5 w-1.5 rounded-full bg-success" />
                            <span className="text-muted-foreground">Online</span>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    )
}
