// Type definitions for Video Analyzer

export interface ClipData {
    clip_index: number;
    timestamp_approx: string;
    vision_score: number;
    audio_energy: number;
    flow_intensity: number;
}

export interface FlowStats {
    mean_flow: number;
    max_flow: number;
    flow_std: number;
    burstiness: number;
}

export interface AnalysisResult {
    success: boolean;
    video_url: string;
    title: string;
    duration_seconds: number;
    upload_date: string | null;

    // Team info
    home_team: string;
    away_team: string;

    // Aggregate scores
    overall_vision_score: number;
    overall_audio_energy: number;
    flow_stats: FlowStats;

    // Timeline
    clip_timeline: ClipData[];

    // Peak moments
    peak_visual_moment: string;
    peak_audio_moment: string;

    // AI report
    ai_scouting_report: string | null;

    // Processing info
    frames_analyzed: number;
    processing_time_seconds: number;
}
