import fs from "fs"
import { type NextRequest, NextResponse } from "next/server"
import path from "path"

export async function GET(request: NextRequest) {
  try {
    const projectRoot = process.cwd()
    const metricsPath = path.join(projectRoot, "data", "metrics", "daily_accuracy.csv")

    // Try to read accuracy from metrics file
    if (!fs.existsSync(metricsPath)) {
      return NextResponse.json({
        success: false,
        accuracy: null,
        total_games: 0,
        total_correct: 0,
        days_evaluated: 0,
        source: "missing",
        message: "Accuracy metrics not found. Run the evaluation pipeline to generate daily_accuracy.csv.",
      }, { status: 404 })
    }

    const content = fs.readFileSync(metricsPath, "utf-8")
    const lines = content.split("\n").filter(line => line.trim())

    if (lines.length <= 1) {
      return NextResponse.json({
        success: false,
        accuracy: null,
        total_games: 0,
        total_correct: 0,
        days_evaluated: 0,
        source: "empty",
        message: "Accuracy metrics file is empty. Run the evaluation pipeline to populate it.",
      }, { status: 404 })
    }

    const header = lines[0].split(",")
    const dataLines = lines.slice(1)

    let totalGames = 0
    let totalCorrect = 0

    for (const line of dataLines) {
      const values = line.split(",")
      const gamesIdx = header.indexOf("total_games")
      const correctIdx = header.indexOf("correct")

      if (gamesIdx !== -1 && values[gamesIdx]) {
        totalGames += parseInt(values[gamesIdx]) || 0
      }
      if (correctIdx !== -1 && values[correctIdx]) {
        totalCorrect += parseInt(values[correctIdx]) || 0
      }
    }

    if (totalGames === 0) {
      return NextResponse.json({
        success: false,
        accuracy: null,
        total_games: totalGames,
        total_correct: totalCorrect,
        days_evaluated: dataLines.length,
        source: "empty",
        message: "No evaluated games found yet.",
      }, { status: 404 })
    }

    const accuracy = (totalCorrect / totalGames) * 100

    return NextResponse.json({
      success: true,
      accuracy: parseFloat(accuracy.toFixed(1)),
      total_games: totalGames,
      total_correct: totalCorrect,
      days_evaluated: dataLines.length,
      source: "metrics_file"
    })

  } catch (error) {
    console.error("Error fetching accuracy data:", error)
    return NextResponse.json({
      success: false,
      accuracy: null,
      total_games: 0,
      total_correct: 0,
      days_evaluated: 0,
      source: "error",
      message: "Failed to fetch accuracy data."
    }, { status: 500 })
  }
}
