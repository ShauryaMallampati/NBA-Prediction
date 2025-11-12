import { type NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const gameId = searchParams.get("game_id")

  if (!gameId) {
    return NextResponse.json(
      { error: "game_id parameter is required" },
      { status: 400 }
    )
  }

  try {
    const url = `${API_URL}/api/explain?game_id=${gameId}`

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching SHAP explanation:", error)
    return NextResponse.json(
      { error: "Failed to fetch SHAP explanation" },
      { status: 500 }
    )
  }
}

