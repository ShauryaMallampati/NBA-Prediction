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
  models_agree?: number | string
  individual_votes?: Record<string, string>
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const dateParam = searchParams.get("date")

    // Use provided date or today's date
    const targetDate = dateParam || new Date().toISOString().split("T")[0]

    const projectRoot = process.cwd()
    const predictionsDir = path.join(projectRoot, "data", "predictions")
    const modelMetaPath = path.join(projectRoot, "artifacts", "models", "pregame", "metadata.json")

    const normalizeProb = (value: number | undefined) => {
      if (typeof value !== "number") return 50
      return value <= 1 ? Math.round(value * 1000) / 10 : value
    }

    const modelInfo = (() => {
      if (!fs.existsSync(modelMetaPath)) return null
      try {
        const meta = JSON.parse(fs.readFileSync(modelMetaPath, "utf-8"))
        const modelNames = meta?.models ? Object.keys(meta.models) : []
        const featureNames = Array.isArray(meta?.feature_names)
          ? meta.feature_names
          : Array.isArray(meta?.feature_columns)
            ? meta.feature_columns
            : []
        return {
          num_models: modelNames.length,
          model_names: modelNames,
          num_features: featureNames.length,
          feature_names: featureNames.length ? featureNames : undefined,
        }
      } catch {
        return null
      }
    })()

    // Check if predictions directory exists
    if (!fs.existsSync(predictionsDir)) {
      return NextResponse.json({
        success: true,
        count: 0,
        total_games: 0,
        date: targetDate,
        predictions: [],
        model_info: modelInfo || undefined,
        timestamp: new Date().toISOString(),
        source: "missing",
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
        model_info: modelInfo || undefined,
        timestamp: new Date().toISOString(),
        source: "empty",
        message: `No predictions found. Run the daily pipeline to generate predictions.`,
      })
    }

    // Read JSONL file
    const filePath = path.join(predictionsDir, targetFile)
    const fileContent = fs.readFileSync(filePath, "utf-8")
    const lines = fileContent.split("\n").filter(line => line.trim())

    const predictions: Prediction[] = lines.map(line => {
      const raw = JSON.parse(line)
      const homeProb = normalizeProb(raw.home_win_prob ?? raw.home_win_probability)
      const awayProb = normalizeProb(raw.away_win_prob ?? raw.away_win_probability)
      const confidence = normalizeProb(raw.confidence ?? Math.max(homeProb, awayProb))
      const homeSpread = raw.home_spread ?? raw.spread
      const awaySpread = raw.away_spread ?? (typeof homeSpread === 'number' ? -homeSpread : undefined)
      const homeOdds = raw.home_odds ?? raw.home_ml
      const awayOdds = raw.away_odds ?? raw.away_ml
      const commenceTime = raw.commence_time || raw.game_time || (raw.date ? `${raw.date}T12:00:00` : '')

      return {
        game_id: raw.game_id || raw.id || `${raw.home_team}-${raw.away_team}`,
        date: raw.date || targetDate,
        home_team: raw.home_team,
        away_team: raw.away_team,
        home_win_prob: homeProb,
        away_win_prob: awayProb,
        predicted_winner: raw.predicted_winner || raw.prediction ||
          (homeProb > awayProb ? raw.home_team : raw.away_team),
        confidence,
        commence_time: commenceTime,
        home_spread: homeSpread,
        away_spread: awaySpread,
        home_odds: homeOdds,
        away_odds: awayOdds,
        models_agree: raw.models_agree,
        individual_votes: raw.individual_votes,
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
      consensus_percentage: p.confidence,
      commence_time: p.commence_time,
      home_spread: p.home_spread,
      home_odds: p.home_odds,
      away_odds: p.away_odds,
      away_spread: p.away_spread,
      individual_votes: p.individual_votes ?? {},
      models_agree: p.models_agree ?? modelInfo?.num_models,
    }))

    return NextResponse.json({
      success: true,
      count: formattedPredictions.length,
      total_games: formattedPredictions.length,
      date: targetFile.replace('.jsonl', ''),
      predictions: formattedPredictions,
      model_info: modelInfo || undefined,
      timestamp: new Date().toISOString(),
      source: "file",
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
