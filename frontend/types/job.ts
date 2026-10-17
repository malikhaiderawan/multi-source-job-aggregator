export interface MatchScoreBreakdown {
    skills_score: number;
    seniority_score: number;
    location_score: number;
    salary_score: number;
    total_score: number;
    matched_skills: string[];
    missing_skills: string[];
    notes: string[];
}

export interface JobPosting {
    id?: string | null;
    title: string;
    company: string;
    location: string;
    salary: string;
    url: string;
    source: string;
    posted_date?: string | null;
    description_snippet?: string;
    category?: 'Mobile' | 'Frontend' | 'Backend' | 'Full-stack' | string;
    is_remote?: boolean;
    country?: string | null;
    seniority_level?: string;
    tags?: string[];
    match_score: number;
    match_breakdown?: MatchScoreBreakdown;
    application_status?: 'saved' | 'pending_approval' | 'applied' | 'interview' | 'rejected' | 'follow_up' | 'untracked';
    location_eligibility?: 'lahore_onsite' | 'lahore_hybrid' | 'pakistan_remote' | 'worldwide_remote' | 'ineligible_region' | 'eligibility_unknown';
    eligibility_detail?: string;
    original_location?: string | null;
    contact_email?: string | null;
}

export interface JobListResponse {
    total_count: number;
    count: number;
    results: JobPosting[];
    categories_count?: Record<string, number>;
    providers_count?: Record<string, number>;
    eligibility_count?: Record<string, number>;
    query_timestamp?: string;
}

export interface JobQuery {
    keyword?: string;
    location?: string;
    category?: string;
    min_score?: number;
    limit?: number;
}

export interface ApplicationTrackerItem {
    id: string;
    candidate_id: string;
    job: JobPosting;
    status: 'saved' | 'pending_approval' | 'applied' | 'interview' | 'rejected' | 'follow_up';
    notes?: string;
    tailored_cv_bullet_points?: string[];
    tailored_cover_letter?: string;
    tailored_recruiter_email?: string;
    email_recipient?: string;
    email_approved?: boolean;
    email_sent?: boolean;
    email_dispatch_mode?: 'none' | 'simulated_dry_run' | 'live_smtp';
    recruiter_email_sent?: boolean;
    official_application_submitted?: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface ApplicationGenerateResponse {
    job_id: string;
    candidate_name: string;
    tailored_cv_bullet_points: string[];
    cover_letter: string;
    recruiter_email: string;
    key_selling_points: string[];
    suggested_recipient_email?: string | null;
}

export interface CandidateProfileMeta {
    id: string;
    is_active: boolean;
    profile: {
        name: string;
        headline: string;
        email: string;
        phone: string;
        location: string;
        github?: string;
        linkedin?: string;
        total_years_experience: number;
        all_skills: string[];
        target_locations: string[];
    };
}

export interface LinkedInSyncResponse {
    status: 'success' | 'missing_credentials' | 'error';
    message: string;
    emails_scanned: number;
    jobs_extracted: number;
    unique_jobs_added: number;
    duplicates_skipped: number;
    failures: number;
    eligibility_count: Record<string, number>;
    jobs: JobPosting[];
}