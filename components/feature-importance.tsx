'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { cn } from '@/lib/utils'

interface FeatureImportanceProps {
  features: Array<{ feature: string; importance: number }>
  maxFeatures?: number
  className?: string
}

export function FeatureImportance({
  features,
  maxFeatures = 5,
  className,
}: FeatureImportanceProps) {
  const topFeatures = [...features]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, maxFeatures)
    .map((feature, index) => ({
      ...feature,
      index: index + 1,
    }))

  const formatFeatureName = (name: string) =>
    name.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

  const chartData = topFeatures.map((feature) => ({
    name: formatFeatureName(feature.feature),
    importance: feature.importance,
  }))

  return (
    <div className={cn('bento-item', className)}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Top {maxFeatures} Features</h3>
        <p className="text-sm text-muted-foreground">Most influential signals behind the prediction.</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis type="number" className="text-muted-foreground" />
          <YAxis type="category" dataKey="name" width={160} className="text-muted-foreground" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
            }}
            formatter={(value) => (typeof value === 'number' ? value.toFixed(3) : value)}
          />
          <Bar dataKey="importance" fill="hsl(var(--foreground))" radius={[0, 8, 8, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 space-y-2">
        {topFeatures.map((feature) => (
          <div
            key={feature.feature}
            className="flex items-center justify-between p-2 rounded-md bg-muted/40"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">#{feature.index}</span>
              <span className="text-sm">{formatFeatureName(feature.feature)}</span>
            </div>
            <span className="text-sm font-semibold">{feature.importance.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
