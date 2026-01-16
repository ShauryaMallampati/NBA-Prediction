import fs from "fs"
import { type NextRequest, NextResponse } from "next/server"
import path from "path"

interface Prediction {
  game_id: string
  date: string
  home_team: string
  away_team: string
  home_win_prob: number
  away_win_prob: number
  predicted_winner: string
  confidence: number
  commence_time?: string
  home_spread?: number
  away_spread?: number
  home_odds?: number
  away_odds?: number
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const dateParam = searchParams.get("date")

    // Use provided date or today's date
    const targetDate = dateParam || new Date().toISOString().split("T")[0]

    const projectRoot = process.cwd()
    const predictionsDir = path.join(projectRoot, "data", "predictions")

    // Check if predictions directory exists
    if (!fs.existsSync(predictionsDir)) {
      return NextResponse.json({
        success: true,
        count: 0,
        total_games: 0,
        date: targetDate,
        predictions: [],
        message: "Predictions directory not found. Run the daily pipeline first.",
      })
    }

    // Try to find a matching JSONL file
    const files = fs.readdirSync(predictionsDir)
    const jsonlFiles = files.filter(f => f.endsWith('.jsonl'))

    // Sort files by date (descending) to get most recent
    jsonlFiles.sort().reverse()

    // Find file matching target date, or use most recent
    let targetFile = jsonlFiles.find(f => f.includes(targetDate))
    if (!targetFile && jsonlFiles.length > 0) {
      targetFile = jsonlFiles[0]  // Use most recent if no exact match
    }

    if (!targetFile) {
      return NextResponse.json({
        success: true,
        count: 0,
        total_games: 0,
        date: targetDate,
        predictions: [],
        message: `No predictions found. The pipeline runs daily at 1:30 AM EST.`,
      })
    }

    // Read JSONL file
    const filePath = path.join(predictionsDir, targetFile)
    const fileContent = fs.readFileSync(filePath, "utf-8")
    const lines = fileContent.split("\n").filter(line => line.trim())

    const predictions: Prediction[] = lines.map(line => {
      const raw = JSON.parse(line)
      return {
        game_id: raw.game_id || raw.id || `${raw.home_team}-${raw.away_team}`,
        date: raw.date || targetDate,
        home_team: raw.home_team,
        away_team: raw.away_team,
        home_win_prob: raw.home_win_prob || raw.home_win_probability || 50,
        away_win_prob: raw.away_win_prob || raw.away_win_probability || 50,
        predicted_winner: raw.predicted_winner || raw.prediction ||
          ((raw.home_win_prob || raw.home_win_probability || 50) > 50 ? raw.home_team : raw.away_team),
        confidence: raw.confidence || Math.max(raw.home_win_prob || 50, raw.away_win_prob || 50),
        commence_time: raw.commence_time || raw.game_time || new Date().toISOString(),
        home_spread: raw.home_spread || raw.spread || 0,
        away_spread: raw.away_spread || -(raw.home_spread || raw.spread || 0),
        home_odds: raw.home_odds || raw.home_ml || -110,
        away_odds: raw.away_odds || raw.away_ml || -110,
      }
    })

    // Transform to expected frontend format
    const formattedPredictions = predictions.map(p => ({
      game_id: p.game_id,
      home_team: p.home_team,
      away_team: p.away_team,
      home_win_probability: p.home_win_prob,
      away_win_probability: p.away_win_prob,
      prediction: p.home_win_prob > p.away_win_prob ? 'HOME_WIN' : 'AWAY_WIN',
      confidence: p.confidence,
      commence_time: p.commence_time,
      home_spread: p.home_spread,
      home_odds: p.home_odds,
      individual_votes: {},
      models_agree: 3,
    }))

    return NextResponse.json({
      success: true,
      count: formattedPredictions.length,
      total_games: formattedPredictions.length,
      date: targetFile.replace('.jsonl', ''),
      predictions: formattedPredictions,
    })

  } catch (error) {
    console.error("Error fetching predictions:", error)
    return NextResponse.json(
      {
        success: false,
        count: 0,
        total_games: 0,
        predictions: [],
        error: "Failed to fetch predictions",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    )
  }
}
