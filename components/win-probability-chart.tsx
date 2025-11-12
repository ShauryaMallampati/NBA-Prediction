"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"
import { cn } from "@/lib/utils"

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
  // Format chart data
  const chartData = data.map((d) => ({
    time: d.time,
    [homeTeam]: d.homeProb * 100,
    [awayTeam]: d.awayProb * 100,
  }))

  return (
    <Card className={cn("p-6 bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700", className)}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Win Probability Over Time</h3>
        <p className="text-sm text-gray-400">Real-time probability shifts</p>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            stroke="#9CA3AF"
            tick={{ fill: "#D1D5DB" }}
          />
          <YAxis
            stroke="#9CA3AF"
            tick={{ fill: "#D1D5DB" }}
            domain={[0, 100]}
            label={{ value: "Win Probability (%)", angle: -90, position: "insideLeft", fill: "#D1D5DB" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#F9FAFB",
            }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <ReferenceLine y={50} stroke="#6B7280" strokeDasharray="2 2" />
          <Line
            type="monotone"
            dataKey={homeTeam}
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ r: 4, fill: "#3B82F6" }}
            name={homeTeam}
          />
          <Line
            type="monotone"
            dataKey={awayTeam}
            stroke="#EF4444"
            strokeWidth={2}
            dot={{ r: 4, fill: "#EF4444" }}
            name={awayTeam}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-sm text-gray-300">{homeTeam}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-sm text-gray-300">{awayTeam}</span>
        </div>
      </div>
    </Card>
  )
}

