"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ConfidenceMeterProps {
  confidence: number // 0-1
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
  className?: string
}

export function ConfidenceMeter({
  confidence,
  size = "md",
  showLabel = true,
  className,
}: ConfidenceMeterProps) {
  // Clamp confidence to 0-1
  const clampedConfidence = Math.max(0, Math.min(1, confidence))
  const percentage = Math.round(clampedConfidence * 100)

  // Size classes
  const sizeClasses = {
    sm: "h-2 w-24",
    md: "h-3 w-32",
    lg: "h-4 w-40",
  }

  // Color based on confidence
  const getColor = (conf: number) => {
    if (conf >= 0.7) return "bg-green-500"
    if (conf >= 0.5) return "bg-yellow-500"
    if (conf >= 0.3) return "bg-orange-500"
    return "bg-red-500"
  }

  // Gradient based on confidence
  const getGradient = (conf: number) => {
    if (conf >= 0.7) return "from-green-500 to-green-600"
    if (conf >= 0.5) return "from-yellow-500 to-yellow-600"
    if (conf >= 0.3) return "from-orange-500 to-orange-600"
    return "from-red-500 to-red-600"
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className={cn("relative overflow-hidden rounded-full bg-gray-200 dark:bg-gray-800", sizeClasses[size])}>
        <motion.div
          className={cn("h-full rounded-full bg-gradient-to-r", getGradient(clampedConfidence))}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {percentage}%
        </span>
      )}
    </div>
  )
}

