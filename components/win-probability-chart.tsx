'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { cn } from '@/lib/utils'

interface WinProbabilityData {
  time: string
  homeProb: number
  awayProb: number
}

interface WinProbabilityChartProps {
  data: WinProbabilityData[]
  homeTeam: string
  awayTeam: string
  className?: string
}

export function WinProbabilityChart({
  data,
  homeTeam,
  awayTeam,
  className,
}: WinProbabilityChartProps) {
  const chartData = data.map((entry) => ({
    time: entry.time,
    [homeTeam]: entry.homeProb * 100,
    [awayTeam]: entry.awayProb * 100,
  }))

  return (
    <div className={cn('bento-item', className)}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Win Probability Over Time</h3>
        <p className="text-sm text-muted-foreground">Real-time probability shifts.</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey="time" className="text-muted-foreground" />
          <YAxis
            className="text-muted-foreground"
            domain={[0, 100]}
            label={{ value: 'Win Probability (%)', angle: -90, position: 'insideLeft', fill: 'hsl(var(--muted-foreground))' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
            formatter={(value) => {
              const numeric = typeof value === 'number' ? value : Number(value)
              return Number.isFinite(numeric) ? `${numeric.toFixed(1)}%` : value
            }}
          />
          <ReferenceLine y={50} stroke="hsl(var(--border))" strokeDasharray="2 2" />
          <Line type="monotone" dataKey={homeTeam} stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey={awayTeam} stroke="hsl(var(--secondary))" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-center gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: 'hsl(var(--primary))' }} />
          {homeTeam}
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: 'hsl(var(--secondary))' }} />
          {awayTeam}
        </div>
      </div>
    </div>
  )
}
