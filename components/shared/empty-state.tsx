import { cn } from '@/lib/utils'
import { AlertCircle, RefreshCw, FileQuestion, Calendar, Target } from 'lucide-react'

interface EmptyStateProps {
    title: string
    description?: string
    icon?: 'empty' | 'calendar' | 'predictions' | 'error'
    action?: {
        label: string
        onClick: () => void
    }
    className?: string
}

const icons = {
    empty: FileQuestion,
    calendar: Calendar,
    predictions: Target,
    error: AlertCircle,
}

export function EmptyState({
    title,
    description,
    icon = 'empty',
    action,
    className,
}: EmptyStateProps) {
    const Icon = icons[icon]

    return (
        <div
            className={cn(
                'flex flex-col items-center justify-center py-16 text-center',
                className
            )}
        >
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
                <Icon className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
            {description && (
                <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
            )}
            {action && (
                <button
                    onClick={action.onClick}
                    className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                    <RefreshCw className="h-4 w-4" />
                    {action.label}
                </button>
            )}
        </div>
    )
}
