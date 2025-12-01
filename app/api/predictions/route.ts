import fs from "fs"
import { type NextRequest, NextResponse } from "next/server"
import path from "path"

interface Prediction {
  game_id: string
  date: string
  home_team: string
  away_team: string
  home_win_prob: string
  away_win_prob: string
  predicted_winner: string
  confidence: string
  top_feature_1: string | null
  top_feature_2: string | null
  top_feature_3: string | null
  generated_at: string
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const date = searchParams.get("date") || new Date().toISOString().split("T")[0]

    // Try to read predictions from CSV file first
    const projectRoot = process.cwd()
    const predictionsPath = path.join(projectRoot, "artifacts", "predictions", `predictions_${date}.csv`)

    if (fs.existsSync(predictionsPath)) {
      // Read CSV file
      const fileContent = fs.readFileSync(predictionsPath, "utf-8")
      const lines = fileContent.split("\n").filter(line => line.trim())
      
      if (lines.length > 1) {
        const headers = lines[0].split(",")
        const predictions: Prediction[] = lines.slice(1).map(line => {
          const values = line.split(",")
          const obj: any = {}
          headers.forEach((header, idx) => {
            obj[header] = values[idx] || null
          })
          // Parse numeric values
          obj.home_win_prob = parseFloat(obj.home_win_prob)
          obj.away_win_prob = parseFloat(obj.away_win_prob)
          obj.confidence = parseFloat(obj.confidence)
          return obj
        })

        return NextResponse.json({
          success: true,
          count: predictions.length,
          date,
          predictions,
        })
      }
    }

    // If no CSV file, return empty
    return NextResponse.json({
      success: false,
      count: 0,
      date,
      predictions: [],
      message: `No predictions found for ${date}. Run: poetry run python scripts/generate_todays_predictions.py`,
    })
  } catch (error) {
    console.error("Error fetching predictions:", error)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch predictions",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    )
  }
}
