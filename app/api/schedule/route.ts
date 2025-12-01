import { NextResponse } from 'next/server'

const RAPIDAPI_KEY = process.env.NEXT_PUBLIC_RAPIDAPI_KEY || 'REMOVED_RAPIDAPI_KEY'
const RAPIDAPI_HOST = 'nba-schedule.p.rapidapi.com'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const month = searchParams.get('month') // YYYY-MM format
    const daysAhead = parseInt(searchParams.get('days') || '14') // Default to 14 days

    // If no month specified, get upcoming games (today through next N days)
    if (!month) {
      // Construct date range
      const today = new Date()
      today.setHours(today.getHours() - 8) // Adjust to PST
      const endDate = new Date(today)
      endDate.setDate(endDate.getDate() + daysAhead)

      const todayStr = today.toISOString().split('T')[0]
      const endDateStr = endDate.toISOString().split('T')[0]

      // Request live schedule from the local FastAPI service (python) which will
      // attempt to use `nba_api` or `pyespn`. This avoids hard-coded RapidAPI usage.
      const backendUrl = process.env.SCHEDULE_BACKEND || 'http://localhost:8000/live_schedule'
      const response = await fetch(`${backendUrl}?days=${daysAhead}`)

      if (!response.ok) {
        console.error('Local schedule service error:', response.status, response.statusText)
        return NextResponse.json({
          success: false,
          message: 'Failed to fetch schedule from local service',
          games: [],
          gamesByDate: {},
          dates: []
        }, { status: response.status })
      }

      const payload = await response.json()
      let games = Array.isArray(payload) ? payload : payload.games || []

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
            game_id: game.id || game.game_id || game.gameId || '',
            date: gameDate,
            home_team: game.home_team || game.homeTeam || game.home || '',
            away_team: game.away_team || game.awayTeam || game.away || '',
            game_time: game.time || game.game_time || game.gameTime || game.startTime || '',
            season: game.season || '2024-25'
          }

          gamesByDate[gameDate].push(normalizedGame)
        }
      })

      return NextResponse.json({
        success: true,
        count: games.length,
        date_range: `${todayStr} to ${endDateStr}`,
        dates: Object.keys(gamesByDate).sort(),
        gamesByDate: gamesByDate,
        games: games
      })
    }

    // Filter by specific month (YYYY-MM format)
    // Fetch full schedule (month) from local backend if available
    const backendUrl = process.env.SCHEDULE_BACKEND || 'http://localhost:8000/live_schedule'
    const response = await fetch(backendUrl)

    if (!response.ok) {
      console.error('Local schedule service error:', response.status, response.statusText)
      return NextResponse.json({
        success: false,
        message: 'Failed to fetch schedule from local service',
        games: [],
        gamesByDate: {},
        dates: []
      }, { status: response.status })
    }

    const payload = await response.json()
    let games = Array.isArray(payload) ? payload : payload.games || payload.games || []

    // Filter by month
    games = games.filter((game: any) => {
      const gameDate = game.date || game.game_date || game.gameDate || ''
      return gameDate.startsWith(month)
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
          game_id: game.id || game.game_id || game.gameId || '',
          date: gameDate,
          home_team: game.home_team || game.homeTeam || game.home || '',
          away_team: game.away_team || game.awayTeam || game.away || '',
          game_time: game.time || game.game_time || game.gameTime || game.startTime || '',
          season: game.season || '2024-25'
        }

        gamesByDate[gameDate].push(normalizedGame)
      }
    })

    return NextResponse.json({
      success: true,
      count: games.length,
      month: month,
      dates: Object.keys(gamesByDate).sort(),
      gamesByDate: gamesByDate,
      games: games
    })
  } catch (error) {
    console.error('Error fetching schedule:', error)
    return NextResponse.json({
      success: false,
      message: 'Failed to load schedule',
      error: error instanceof Error ? error.message : 'Unknown error',
      games: [],
      gamesByDate: {},
      dates: []
    }, { status: 500 })
  }
}
