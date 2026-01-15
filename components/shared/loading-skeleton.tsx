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
        <div className="bento-item space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-16" />
        </div>
    )
}

export function TableRowSkeleton() {
    return (
        <div className="flex items-center gap-4 p-4 border-b border-border">
            <Skeleton className="h-8 w-8 rounded-md" />
            <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-3 w-1/3" />
            </div>
            <Skeleton className="h-6 w-16 rounded-md" />
        </div>
    )
}

export function PredictionCardSkeleton() {
    return (
        <div className="bento-item p-5 space-y-4">
            <div className="flex items-center justify-between">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-5 w-12 rounded-md" />
            </div>
            <div className="grid grid-cols-3 gap-2 items-center">
                <div className="space-y-2 text-right">
                    <Skeleton className="h-2 w-10 ml-auto" />
                    <Skeleton className="h-5 w-20 ml-auto" />
                </div>
                <div className="text-center">
                    <Skeleton className="h-6 w-16 mx-auto" />
                    <Skeleton className="h-1.5 w-full mt-2 rounded-full" />
                </div>
                <div className="space-y-2">
                    <Skeleton className="h-2 w-10" />
                    <Skeleton className="h-5 w-20" />
                </div>
            </div>
        </div>
    )
}

export function PageSkeleton() {
    return (
        <div className="space-y-6">
            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <CardSkeleton key={i} />
                ))}
            </div>
            {/* Content */}
            <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                    <PredictionCardSkeleton key={i} />
                ))}
            </div>
        </div>
    )
}
