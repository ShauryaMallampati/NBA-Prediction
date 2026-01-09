import { cn } from '@/lib/utils'
import { type LucideIcon } from 'lucide-react'

interface KPICardProps {
    title: string
    value: string | number
    icon?: LucideIcon
    trend?: {
        value: number
        isPositive: boolean
    }
    className?: string
    valueClassName?: string
}

export function KPICard({
    title,
    value,
    icon: Icon,
    trend,
    className,
    valueClassName,
}: KPICardProps) {
    return (
        <div className={cn('rounded-xl border border-border bg-card p-4', className)}>
            <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{title}</span>
                {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
            </div>
            <div className="mt-2 flex items-baseline gap-2">
                <span className={cn('text-2xl font-bold', valueClassName)}>{value}</span>
                {trend && (
                    <span
                        className={cn(
                            'text-xs font-medium',
                            trend.isPositive ? 'text-green-500' : 'text-red-500'
                        )}
                    >
                        {trend.isPositive ? '+' : ''}{trend.value}%
                    </span>
                )}
            </div>
        </div>
    )
}
