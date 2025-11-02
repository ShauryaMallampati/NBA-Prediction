'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Zap, AlertCircle, Home, Users } from 'lucide-react';

interface LiveGame {
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  time_remaining: string;
  home_win_prob: number;
  away_win_prob: number;
  prob_change: number;
  key_events: string[];
  status: 'live' | 'scheduled' | 'final';
}

export default function LivePage() {
  const [games, setGames] = useState<LiveGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);

  useEffect(() => {
    const fetchLiveGames = async () => {
      try {
        const response = await fetch('/api/games/live');
        if (response.ok) {
          const data = await response.json();
          setGames(Array.isArray(data) ? data : data.games || []);
          if (!selectedGameId && data.length > 0) {
            setSelectedGameId((Array.isArray(data) ? data[0] : data.games?.[0])?.game_id);
          }
        }
      } catch (error) {
        console.error('Failed to fetch live games:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLiveGames();
    // Refresh every 30 seconds
    const interval = setInterval(fetchLiveGames, 30 * 1000);
    return () => clearInterval(interval);
  }, [selectedGameId]);

  const selectedGame = games.find(g => g.game_id === selectedGameId);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="text-center py-12">
          <Zap className="w-12 h-12 text-cyan-400 mx-auto mb-4 animate-pulse" />
          <p className="text-slate-400">Loading live games...</p>
        </div>
      </div>
    );
  }

  const liveGames = games.filter(g => g.status === 'live');
  const scheduledGames = games.filter(g => g.status === 'scheduled');
  const finalGames = games.filter(g => g.status === 'final');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🔴 Live Games</h1>
          <div className="flex items-center gap-4 text-slate-400">
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
              {liveGames.length} Live
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
              {scheduledGames.length} Today
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-slate-500"></span>
              {finalGames.length} Final
            </span>
          </div>
        </div>

        {liveGames.length === 0 && scheduledGames.length === 0 && finalGames.length === 0 ? (
          <div className="text-center py-12 bg-slate-800/30 rounded-lg border border-slate-700">
            <Zap className="w-8 h-8 mx-auto mb-2 opacity-50 text-slate-400" />
            <p className="text-slate-400">No games today</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Games List Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
                <div className="p-4 bg-gradient-to-r from-red-500/20 to-slate-800/50 border-b border-slate-700">
                  <p className="text-sm font-semibold text-white">📺 All Games</p>
                </div>
                <div className="space-y-2 p-4 max-h-96 overflow-y-auto">
                  {/* Live Games */}
                  {liveGames.map(game => (
                    <GameListItem
                      key={game.game_id}
                      game={game}
                      isSelected={selectedGameId === game.game_id}
                      onClick={() => setSelectedGameId(game.game_id)}
                      status="live"
                    />
                  ))}
                  
                  {/* Scheduled Games */}
                  {scheduledGames.length > 0 && (
                    <>
                      {liveGames.length > 0 && <div className="border-t border-slate-700/50 my-2"></div>}
                      {scheduledGames.map(game => (
                        <GameListItem
                          key={game.game_id}
                          game={game}
                          isSelected={selectedGameId === game.game_id}
                          onClick={() => setSelectedGameId(game.game_id)}
                          status="scheduled"
                        />
                      ))}
                    </>
                  )}

                  {/* Final Games */}
                  {finalGames.length > 0 && (
                    <>
                      {(liveGames.length > 0 || scheduledGames.length > 0) && <div className="border-t border-slate-700/50 my-2"></div>}
                      {finalGames.map(game => (
                        <GameListItem
                          key={game.game_id}
                          game={game}
                          isSelected={selectedGameId === game.game_id}
                          onClick={() => setSelectedGameId(game.game_id)}
                          status="final"
                        />
                      ))}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Main Game View */}
            {selectedGame && (
              <div className="lg:col-span-2">
                <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-700/50 rounded-lg overflow-hidden">
                  {/* Game Header */}
                  <div className={`p-6 border-b border-slate-700/50 ${
                    selectedGame.status === 'live' 
                      ? 'bg-gradient-to-r from-red-500/20 to-slate-800/50' 
                      : 'bg-slate-700/30'
                  }`}>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h2 className="text-2xl font-bold text-white mb-1">
                          {selectedGame.home_team} vs {selectedGame.away_team}
                        </h2>
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          {selectedGame.status === 'live' && (
                            <>
                              <span className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                Q{selectedGame.quarter} • {selectedGame.time_remaining}
                              </span>
                            </>
                          )}
                          {selectedGame.status === 'scheduled' && (
                            <span>Coming up today</span>
                          )}
                          {selectedGame.status === 'final' && (
                            <span className="text-slate-500">Final</span>
                          )}
                        </div>
                      </div>
                      <div className={`px-4 py-2 rounded-lg font-bold text-lg ${
                        selectedGame.status === 'live'
                          ? 'bg-red-500/20 text-red-400 animate-pulse'
                          : 'bg-slate-700/50 text-slate-400'
                      }`}>
                        {selectedGame.status === 'live' ? '🔴 LIVE' : selectedGame.status === 'scheduled' ? '⏳ SOON' : '✓ FINAL'}
                      </div>
                    </div>
                  </div>

                  {/* Scoreboard */}
                  <div className="p-6 border-b border-slate-700/50">
                    <div className="grid grid-cols-2 gap-6 mb-4">
                      {/* Home Team */}
                      <div className="bg-gradient-to-br from-cyan-500/20 to-blue-600/10 border border-cyan-500/30 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-4">
                          <Home className="w-5 h-5 text-cyan-400" />
                          <h3 className="text-xl font-bold text-white">{selectedGame.home_team}</h3>
                        </div>
                        <div className="text-5xl font-bold text-cyan-400 mb-4">
                          {selectedGame.home_score}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-400">Win Probability</span>
                          <span className="text-2xl font-bold text-cyan-400">
                            {(selectedGame.home_win_prob * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* Away Team */}
                      <div className="bg-gradient-to-br from-orange-500/20 to-red-600/10 border border-orange-500/30 rounded-lg p-6">
                        <div className="flex items-center gap-3 mb-4">
                          <Users className="w-5 h-5 text-orange-400" />
                          <h3 className="text-xl font-bold text-white">{selectedGame.away_team}</h3>
                        </div>
                        <div className="text-5xl font-bold text-orange-400 mb-4">
                          {selectedGame.away_score}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-400">Win Probability</span>
                          <span className="text-2xl font-bold text-orange-400">
                            {(selectedGame.away_win_prob * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Win Probability Bars */}
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs font-semibold text-slate-400">{selectedGame.home_team}</span>
                          <span className="text-xs font-semibold text-cyan-400">{(selectedGame.home_win_prob * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-slate-700/30 rounded-full h-4 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${selectedGame.home_win_prob * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs font-semibold text-slate-400">{selectedGame.away_team}</span>
                          <span className="text-xs font-semibold text-orange-400">{(selectedGame.away_win_prob * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-slate-700/30 rounded-full h-4 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-orange-400 to-red-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${selectedGame.away_win_prob * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Key Events */}
                  {selectedGame.key_events && selectedGame.key_events.length > 0 && (
                    <div className="p-6">
                      <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-400" />
                        Key Moments
                      </h4>
                      <div className="space-y-2">
                        {selectedGame.key_events.map((event, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg border border-slate-600/50"
                          >
                            <TrendingUp className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                            <span className="text-sm text-slate-300">{event}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function GameListItem({
  game,
  isSelected,
  onClick,
  status,
}: {
  game: LiveGame;
  isSelected: boolean;
  onClick: () => void;
  status: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full p-3 rounded-lg transition-all text-left border ${
        isSelected
          ? 'bg-cyan-500/20 border-cyan-500/50 shadow-lg shadow-cyan-500/20'
          : 'bg-slate-700/30 border-slate-600/30 hover:border-slate-600/60'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="font-semibold text-white text-sm">{game.home_team}</p>
        {status === 'live' && (
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
        )}
      </div>
      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
        <span>vs {game.away_team}</span>
        {status === 'final' && <span className="text-slate-500">Final</span>}
      </div>
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <span className="font-bold text-white">{game.home_score}</span>
          <span className="text-slate-500">-</span>
          <span className="font-bold text-white">{game.away_score}</span>
        </div>
        {status === 'live' && (
          <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
            Q{game.quarter}
          </span>
        )}
      </div>
    </button>
  );
}
