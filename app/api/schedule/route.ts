import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'
import { parse } from 'csv-parse/sync'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const date = searchParams.get('date')
    const month = searchParams.get('month')
    
    const csvPath = path.join(process.cwd(), 'data/schedules/full_season_schedule_2024-25.csv')
    
    if (!fs.existsSync(csvPath)) {
      return NextResponse.json({
        success: false,
        message: 'Schedule data not found',
        games: []
      })
    }

    const fileContent = fs.readFileSync(csvPath, 'utf-8')
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true
    })

    let filteredGames = records

    // Filter by specific date
    if (date) {
      filteredGames = records.filter((game: any) => game.date === date)
    }
    
    // Filter by month (YYYY-MM format)
    if (month) {
      filteredGames = records.filter((game: any) => game.date.startsWith(month))
    }

    // Group games by date
    const gamesByDate: { [key: string]: any[] } = {}
    filteredGames.forEach((game: any) => {
      if (!gamesByDate[game.date]) {
        gamesByDate[game.date] = []
      }
      gamesByDate[game.date].push(game)
    })

    return NextResponse.json({
      success: true,
      count: filteredGames.length,
      dates: Object.keys(gamesByDate).sort(),
      gamesByDate: gamesByDate,
      games: filteredGames
    })
  } catch (error) {
    console.error('Error reading schedule:', error)
    return NextResponse.json({
      success: false,
      message: 'Failed to load schedule',
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}
