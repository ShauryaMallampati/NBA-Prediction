'use client';

import React from 'react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import { ClipData } from './types';

interface AnalysisChartsProps {
    clipTimeline: ClipData[];
}

export function AnalysisCharts({ clipTimeline }: AnalysisChartsProps) {
    // Transform data for charts
    const chartData = clipTimeline.map((clip, idx) => ({
        name: clip.timestamp_approx,
        vision: Math.round(clip.vision_score * 100),
        audio: Math.round(clip.audio_energy * 100),
        flow: clip.flow_intensity,
        index: idx,
    }));

    return (
        <div className="space-y-8 mb-8">
            {/* Visual Dominance Timeline */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    📊 Visual Dominance Over Time
                </h4>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="visionGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis
                                dataKey="name"
                                stroke="#666"
                                tick={{ fill: '#888', fontSize: 12 }}
                                interval={Math.floor(chartData.length / 8)}
                            />
                            <YAxis
                                stroke="#666"
                                tick={{ fill: '#888', fontSize: 12 }}
                                domain={[0, 100]}
                                tickFormatter={(v) => `${v}%`}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1a1a1a',
                                    border: '1px solid #333',
                                    borderRadius: '8px',
                                }}
                                labelStyle={{ color: '#fff' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="vision"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                fill="url(#visionGradient)"
                                name="Visual Score"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                    Higher values indicate stronger visual dominance (paint presence, shot selection)
                </p>
            </div>

            {/* Crowd Energy + Flow */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Crowd Energy */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        🎵 Crowd Energy Timeline
                    </h4>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="audioGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis
                                    dataKey="name"
                                    stroke="#666"
                                    tick={{ fill: '#888', fontSize: 10 }}
                                    interval={Math.floor(chartData.length / 6)}
                                />
                                <YAxis
                                    stroke="#666"
                                    tick={{ fill: '#888', fontSize: 10 }}
                                    domain={[0, 100]}
                                    tickFormatter={(v) => `${v}%`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1a1a1a',
                                        border: '1px solid #333',
                                        borderRadius: '8px',
                                    }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="audio"
                                    stroke="#a855f7"
                                    strokeWidth={2}
                                    fill="url(#audioGradient)"
                                    name="Crowd Energy"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Optical Flow Intensity */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        ⚡ Game Intensity (Optical Flow)
                    </h4>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis
                                    dataKey="name"
                                    stroke="#666"
                                    tick={{ fill: '#888', fontSize: 10 }}
                                    interval={Math.floor(chartData.length / 6)}
                                />
                                <YAxis
                                    stroke="#666"
                                    tick={{ fill: '#888', fontSize: 10 }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1a1a1a',
                                        border: '1px solid #333',
                                        borderRadius: '8px',
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="flow"
                                    stroke="#f97316"
                                    strokeWidth={2}
                                    dot={false}
                                    name="Flow Intensity"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Combined View */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    📈 All Metrics Combined
                </h4>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis
                                dataKey="name"
                                stroke="#666"
                                tick={{ fill: '#888', fontSize: 12 }}
                                interval={Math.floor(chartData.length / 8)}
                            />
                            <YAxis
                                stroke="#666"
                                tick={{ fill: '#888', fontSize: 12 }}
                                domain={[0, 100]}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1a1a1a',
                                    border: '1px solid #333',
                                    borderRadius: '8px',
                                }}
                            />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="vision"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={false}
                                name="Visual"
                            />
                            <Line
                                type="monotone"
                                dataKey="audio"
                                stroke="#a855f7"
                                strokeWidth={2}
                                dot={false}
                                name="Audio"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
