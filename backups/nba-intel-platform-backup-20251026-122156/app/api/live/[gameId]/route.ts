import { type NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function GET(request: NextRequest, { params }: { params: { gameId: string } }) {
  try {
    const response = await fetch(`${API_URL}/live/${params.gameId}`, {
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
    console.error("Error fetching live game data:", error)
    return NextResponse.json({ error: "Failed to fetch live game data" }, { status: 500 })
  }
}
