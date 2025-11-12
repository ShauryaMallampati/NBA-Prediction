"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { cn } from "@/lib/utils"

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
  // Sort by importance and take top N
  const topFeatures = features
    .sort((a, b) => b.importance - a.importance)
    .slice(0, maxFeatures)
    .map((f, i) => ({
      ...f,
      index: i + 1,
    }))

  // Format feature names (remove underscores, capitalize)
  const formatFeatureName = (name: string) => {
    return name
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase())
  }

  // Chart data
  const chartData = topFeatures.map((f) => ({
    name: formatFeatureName(f.feature),
    importance: f.importance,
  }))

  return (
    <Card className={cn("p-6 bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700", className)}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Top {maxFeatures} Features</h3>
        <p className="text-sm text-gray-400">Most important factors in this prediction</p>
      </div>

      {/* Bar Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" stroke="#9CA3AF" />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#9CA3AF"
            width={150}
            tick={{ fill: "#D1D5DB" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#F9FAFB",
            }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Bar
            dataKey="importance"
            fill="#3B82F6"
            radius={[0, 8, 8, 0]}
          >
            {chartData.map((entry, index) => (
              <motion.cell
                key={`cell-${index}`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Feature List */}
      <div className="mt-4 space-y-2">
        {topFeatures.map((f, index) => (
          <motion.div
            key={f.feature}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-400">#{f.index}</span>
              <span className="text-sm text-white">{formatFeatureName(f.feature)}</span>
            </div>
            <span className="text-sm font-semibold text-blue-400">
              {f.importance.toFixed(3)}
            </span>
          </motion.div>
        ))}
      </div>
    </Card>
  )
}

