'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    Brain,
    Calendar,
    FlaskConical,
    Home,
    Menu,
    Settings,
    Target,
    Users,
    X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Predictions', href: '/predictions', icon: Target },
    { name: 'Schedule', href: '/schedule', icon: Calendar },
    { name: 'Teams', href: '/teams', icon: Users },
    { name: 'Analysis', href: '/analysis', icon: Brain },
    { name: 'Chemistry', href: '/chemistry', icon: FlaskConical },
    { name: 'Settings', href: '/settings', icon: Settings },
]

export function MobileNav() {
    const [open, setOpen] = useState(false)
    const pathname = usePathname()

    return (
        <>
            {/* Mobile header - Clean, no gradients */}
            <div className="lg:hidden fixed top-0 left-0 right-0 z-50 flex h-16 items-center justify-between border-b border-border bg-card px-4">
                <Link href="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-md bg-foreground flex items-center justify-center">
                        <span className="text-background font-bold text-xs">NBA</span>
                    </div>
                    <span className="font-semibold">NBA Intel</span>
                </Link>
                <button
                    onClick={() => setOpen(!open)}
                    className="p-2 rounded-md hover:bg-accent transition-colors"
                >
                    {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </button>
            </div>

            {/* Mobile menu overlay */}
            {open && (
                <div className="lg:hidden fixed inset-0 z-40">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
                        onClick={() => setOpen(false)}
                    />

                    {/* Menu panel */}
                    <div className="absolute inset-y-0 left-0 w-full max-w-xs bg-card border-r border-border pt-20 px-4">
                        <nav className="space-y-1">
                            {navigation.map((item) => {
                                const isActive = pathname === item.href
                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        onClick={() => setOpen(false)}
                                        className={cn(
                                            'flex items-center gap-3 rounded-md px-3 py-3 text-base font-medium transition-colors',
                                            isActive
                                                ? 'bg-foreground text-background'
                                                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                        )}
                                    >
                                        <item.icon className="h-5 w-5" />
                                        {item.name}
                                    </Link>
                                )
                            })}
                        </nav>
                    </div>
                </div>
            )}
        </>
    )
}
