'use client';

import React, { useState } from 'react';
import { AnalysisCharts } from '@/components/analyze/AnalysisCharts';
import { AnalysisResult, ClipData } from '@/components/analyze/types';

export default function AnalyzePage() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);

    const handleAnalyze = async () => {
        if (!url.trim()) {
            setError('Please enter a YouTube URL');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, generate_report: true }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Analysis failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Analysis failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🏀</span>
                        <h1 className="text-xl font-semibold">NBA Video Intelligence</h1>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-6 py-12">
                {/* Input Section */}
                <section className="max-w-3xl mx-auto mb-16">
                    <div className="text-center mb-8">
                        <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            Analyze Any NBA Highlight
                        </h2>
                        <p className="text-gray-400 text-lg">
                            Paste a YouTube link and get AI-powered insights in seconds
                        </p>
                    </div>

                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="https://youtube.com/watch?v=..."
                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                            disabled={loading}
                        />
                        <button
                            onClick={handleAnalyze}
                            disabled={loading}
                            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-semibold hover:from-blue-500 hover:to-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Analyzing...
                                </span>
                            ) : (
                                'Analyze'
                            )}
                        </button>
                    </div>

                    {error && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                            {error}
                        </div>
                    )}
                </section>

                {/* Loading State */}
                {loading && (
                    <section className="max-w-4xl mx-auto text-center py-20">
                        <div className="inline-block">
                            <div className="relative">
                                <div className="w-20 h-20 border-4 border-white/10 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-20 h-20 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                            </div>
                        </div>
                        <p className="mt-6 text-gray-400">
                            Downloading video and running AI analysis...
                        </p>
                        <p className="text-sm text-gray-500 mt-2">
                            This typically takes 60-90 seconds
                        </p>
                    </section>
                )}

                {/* Results */}
                {result && !loading && (
                    <section className="max-w-6xl mx-auto">
                        {/* Game Header */}
                        <div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-2xl p-8 mb-8">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-3xl font-bold mb-2">
                                        {result.away_team} @ {result.home_team}
                                    </h3>
                                    <p className="text-gray-400">{result.title}</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm text-gray-500">Analysis Complete</div>
                                    <div className="text-lg font-semibold text-green-400">
                                        {result.frames_analyzed} frames analyzed
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        in {result.processing_time_seconds}s
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                            <MetricCard
                                icon="🎯"
                                title="Visual Dominance"
                                value={`${(result.overall_vision_score * 100).toFixed(1)}%`}
                                description="CNN-derived game control score"
                                color="blue"
                            />
                            <MetricCard
                                icon="🎵"
                                title="Crowd Energy"
                                value={`${(result.overall_audio_energy * 100).toFixed(1)}%`}
                                description="Audio-based momentum indicator"
                                color="purple"
                            />
                            <MetricCard
                                icon="⚡"
                                title="Game Intensity"
                                value={result.flow_stats.burstiness.toFixed(1) + 'x'}
                                description="Optical flow variance"
                                color="orange"
                            />
                        </div>

                        {/* Charts */}
                        <AnalysisCharts clipTimeline={result.clip_timeline} />

                        {/* Peak Moments */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                                <h4 className="text-sm font-medium text-gray-400 mb-2">Peak Visual Moment</h4>
                                <p className="text-2xl font-bold">{result.peak_visual_moment}</p>
                                <p className="text-sm text-gray-500 mt-1">Highest dominance detected</p>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                                <h4 className="text-sm font-medium text-gray-400 mb-2">Peak Crowd Roar</h4>
                                <p className="text-2xl font-bold">{result.peak_audio_moment}</p>
                                <p className="text-sm text-gray-500 mt-1">Loudest arena moment</p>
                            </div>
                        </div>

                        {/* AI Scouting Report */}
                        {result.ai_scouting_report && (
                            <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-8">
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="text-2xl">🧠</span>
                                    <h4 className="text-xl font-semibold">AI Scouting Report</h4>
                                </div>
                                <p className="text-lg text-gray-300 leading-relaxed">
                                    {result.ai_scouting_report}
                                </p>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-4 justify-center mt-12">
                            <button className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors">
                                📥 Download PDF
                            </button>
                            <button
                                className="px-6 py-3 bg-[#1DA1F2]/20 border border-[#1DA1F2]/30 text-[#1DA1F2] rounded-xl hover:bg-[#1DA1F2]/30 transition-colors"
                                onClick={() => {
                                    const text = `Just analyzed ${result.away_team} @ ${result.home_team} with AI! 🏀\n\nVisual Dominance: ${(result.overall_vision_score * 100).toFixed(0)}%\nCrowd Energy: ${(result.overall_audio_energy * 100).toFixed(0)}%\n\n#NBA #AI`;
                                    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, '_blank');
                                }}
                            >
                                🐦 Share on Twitter
                            </button>
                            <button
                                className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors"
                                onClick={() => {
                                    setResult(null);
                                    setUrl('');
                                }}
                            >
                                🔄 Analyze Another
                            </button>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

function MetricCard({
    icon,
    title,
    value,
    description,
    color,
}: {
    icon: string;
    title: string;
    value: string;
    description: string;
    color: 'blue' | 'purple' | 'orange';
}) {
    const gradients = {
        blue: 'from-blue-500/20 to-blue-500/5',
        purple: 'from-purple-500/20 to-purple-500/5',
        orange: 'from-orange-500/20 to-orange-500/5',
    };

    return (
        <div className={`bg-gradient-to-br ${gradients[color]} border border-white/10 rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">{icon}</span>
                <h4 className="font-medium text-gray-300">{title}</h4>
            </div>
            <p className="text-4xl font-bold mb-2">{value}</p>
            <p className="text-sm text-gray-500">{description}</p>
        </div>
    );
}
