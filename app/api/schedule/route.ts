import fs from "fs"
import { NextResponse } from 'next/server'
import path from "path"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const daysAhead = parseInt(searchParams.get('days') || '14')

    const projectRoot = process.cwd()
    const schedulesDir = path.join(projectRoot, "data", "schedules")

    // Construct date range
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]
    const endDate = new Date(today)
    endDate.setDate(endDate.getDate() + daysAhead)
    const endDateStr = endDate.toISOString().split('T')[0]

    let games: any[] = []

    // Check for schedules directory
    if (fs.existsSync(schedulesDir)) {
      // Try upcoming_14_days.json first
      const upcomingPath = path.join(schedulesDir, "upcoming_14_days.json")
      if (fs.existsSync(upcomingPath)) {
        const content = fs.readFileSync(upcomingPath, "utf-8")
        const data = JSON.parse(content)
        games = Array.isArray(data) ? data : data.games || []
      } else {
        // Try to find any schedule file
        const files = fs.readdirSync(schedulesDir).filter(f => f.endsWith('.json'))
        for (const file of files) {
          const content = fs.readFileSync(path.join(schedulesDir, file), "utf-8")
          const data = JSON.parse(content)
          const fileGames = Array.isArray(data) ? data : data.games || []
          games = [...games, ...fileGames]
        }
      }
    }

    // Also check the main data directory for nba_season_schedule
    const seasonSchedulePath = path.join(projectRoot, "data", "nba_season_schedule_2025_26.json")
    if (games.length === 0 && fs.existsSync(seasonSchedulePath)) {
      const content = fs.readFileSync(seasonSchedulePath, "utf-8")
      const data = JSON.parse(content)
      games = Array.isArray(data) ? data : data.games || []
    }

    // Filter for games within our date range
    games = games.filter((game: any) => {
      const gameDate = game.date || game.game_date || game.gameDate || ''
      return gameDate >= todayStr && gameDate <= endDateStr
    })

    // Group games by date
    const gamesByDate: { [key: string]: any[] } = {}
    games.forEach((game: any) => {
      const gameDate = game.date || game.game_date || game.gameDate || ''
      if (gameDate) {
        if (!gamesByDate[gameDate]) {
          gamesByDate[gameDate] = []
        }

        // Normalize the game object
        const normalizedGame = {
          game_id: game.id || game.game_id || game.gameId || `${game.home_team}-${game.away_team}-${gameDate}`,
          date: gameDate,
          home_team: game.home_team || game.homeTeam || game.home || '',
          away_team: game.away_team || game.awayTeam || game.away || '',
          game_time: game.time || game.game_time || game.gameTime || game.startTime || '',
          season: game.season || ''
        }

        gamesByDate[gameDate].push(normalizedGame)
      }
    })

    return NextResponse.json({
      success: true,
      source: games.length ? 'local' : 'empty',
      count: games.length,
      date_range: `${todayStr} to ${endDateStr}`,
      dates: Object.keys(gamesByDate).sort(),
      gamesByDate: gamesByDate,
      games: games
    })

  } catch (error) {
    console.error('Error fetching schedule:', error)
    return NextResponse.json({
      success: true,
      count: 0,
      source: 'error',
      message: 'No schedule data available. Run the daily pipeline first.',
      games: [],
      gamesByDate: {},
      dates: []
    })
  }
}
