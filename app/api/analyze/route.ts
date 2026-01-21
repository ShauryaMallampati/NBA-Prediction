import { NextRequest, NextResponse } from 'next/server';

/**
 * API Route for video analysis.
 * 
 * This proxies requests to the Python FastAPI backend.
 * In production, you would run the FastAPI server separately.
 */

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // Validate URL
        if (!body.url || typeof body.url !== 'string') {
            return NextResponse.json(
                { detail: 'URL is required' },
                { status: 400 }
            );
        }

        // Check if it's a valid YouTube URL
        const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
        if (!youtubePattern.test(body.url)) {
            return NextResponse.json(
                { detail: 'Please enter a valid YouTube URL' },
                { status: 400 }
            );
        }

        // Forward to FastAPI backend
        const response = await fetch(`${FASTAPI_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: body.url,
                generate_report: body.generate_report ?? true,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            return NextResponse.json(
                { detail: data.detail || 'Analysis failed' },
                { status: response.status }
            );
        }

        return NextResponse.json(data);

    } catch (error) {
        console.error('Analysis error:', error);

        // Check if FastAPI server is running
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                {
                    detail: 'Analysis backend is not running. Start the FastAPI server with: python src/api/video_analyzer.py'
                },
                { status: 503 }
            );
        }

        return NextResponse.json(
            { detail: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function GET() {
    return NextResponse.json({
        status: 'ok',
        message: 'Video Analyzer API - Use POST to analyze videos',
        endpoints: {
            'POST /api/analyze': {
                body: {
                    url: 'YouTube video URL',
                    generate_report: 'boolean (optional, default: true)',
                },
            },
        },
    });
}
