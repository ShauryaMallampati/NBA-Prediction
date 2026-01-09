import { cn } from '@/lib/utils'

interface SkeletonProps {
    className?: string
}

export function Skeleton({ className }: SkeletonProps) {
    return (
        <div
            className={cn('animate-pulse rounded-md bg-muted', className)}
        />
    )
}

export function CardSkeleton() {
    return (
        <div className="rounded-xl border border-border bg-card p-4 space-y-3">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-8 w-1/2" />
        </div>
    )
}

export function TableRowSkeleton() {
    return (
        <div className="flex items-center gap-4 p-4 border-b border-border">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-3 w-1/3" />
            </div>
            <Skeleton className="h-8 w-20 rounded-lg" />
        </div>
    )
}

export function PredictionCardSkeleton() {
    return (
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-6 w-24 rounded-full" />
            </div>
            <div className="flex items-center gap-4">
                <div className="flex-1 p-4 rounded-lg border border-border space-y-2">
                    <Skeleton className="h-3 w-12" />
                    <Skeleton className="h-6 w-20" />
                </div>
                <Skeleton className="h-4 w-8" />
                <div className="flex-1 p-4 rounded-lg border border-border space-y-2">
                    <Skeleton className="h-3 w-12" />
                    <Skeleton className="h-6 w-20" />
                </div>
            </div>
        </div>
    )
}

export function PageSkeleton() {
    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <CardSkeleton key={i} />
                ))}
            </div>
            {/* Content */}
            <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                    <PredictionCardSkeleton key={i} />
                ))}
            </div>
        </div>
    )
}
