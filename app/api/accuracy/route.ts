import { type NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const team = searchParams.get("team")
  const startDate = searchParams.get("start_date")
  const endDate = searchParams.get("end_date")
  const confidenceLevel = searchParams.get("confidence_level")

  try {
    // Build query string
    const params = new URLSearchParams()
    if (team) params.append("team", team)
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (confidenceLevel) params.append("confidence_level", confidenceLevel)

    const url = `${API_URL}/api/accuracy?${params.toString()}`

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
    console.error("Error fetching accuracy data:", error)
    return NextResponse.json(
      { error: "Failed to fetch accuracy data" },
      { status: 500 }
    )
  }
}

