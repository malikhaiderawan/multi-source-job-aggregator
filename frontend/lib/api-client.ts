import {
    JobPosting,
    JobListResponse,
    ApplicationTrackerItem,
    ApplicationGenerateResponse,
    CandidateProfileMeta,
    LinkedInSyncResponse
} from "@/types/job";

const GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FetchJobsParams {
    keyword?: string;
    location?: string;
    category?: string;
    eligibility?: string;
    minScore?: number;
    limit?: number;
}

export async function fetchLiveJobs({
    keyword = "",
    location = "",
    category = "All",
    eligibility = "",
    minScore = 0,
    limit = 100,
}: FetchJobsParams = {}): Promise<JobListResponse> {
    const params = new URLSearchParams();
    if (keyword) params.append("keyword", keyword);
    if (location) params.append("location", location);
    if (category && category !== "All") params.append("category", category);
    if (eligibility && eligibility !== "all") params.append("eligibility", eligibility);
    if (minScore > 0) params.append("min_score", minScore.toString());
    params.append("limit", limit.toString());

    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/jobs?${params.toString()}`, {
            cache: "no-store",
        });

        if (res.ok) {
            return await res.json();
        }
        throw new Error(`Gateway returned HTTP ${res.status}`);
    } catch (err) {
        console.error("Failed to fetch jobs from FastAPI gateway:", err);
        return {
            total_count: 0,
            count: 0,
            results: [],
            categories_count: {},
            providers_count: {},
        };
    }
}

// ==========================================
// Candidate Profile Management Calls
// ==========================================

export async function fetchProfiles(): Promise<CandidateProfileMeta[]> {
    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/profiles`, { cache: "no-store" });
        if (res.ok) return await res.json();
        return [];
    } catch (err) {
        console.error("Error fetching profiles:", err);
        return [];
    }
}

export async function fetchActiveProfile(): Promise<CandidateProfileMeta | null> {
    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/profiles/active`, { cache: "no-store" });
        if (res.ok) return await res.json();
        return null;
    } catch (err) {
        console.error("Error fetching active profile:", err);
        return null;
    }
}

export async function activateProfile(profileId: string): Promise<CandidateProfileMeta | null> {
    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/profiles/${encodeURIComponent(profileId)}/activate`, {
            method: "PUT",
        });
        if (res.ok) return await res.json();
        return null;
    } catch (err) {
        console.error("Error activating profile:", err);
        return null;
    }
}

export async function createCandidateProfile(payload: {
    id: string;
    name: string;
    headline: string;
    email: string;
    phone: string;
    location: string;
    total_years_experience: number;
    all_skills: string[];
    activate?: boolean;
}): Promise<CandidateProfileMeta | null> {
    const res = await fetch(`${GATEWAY_URL}/api/v1/profiles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (res.ok) return await res.json();
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${res.status}: Failed to create candidate profile`);
}

// ==========================================
// Application Tracker Client Calls
// ==========================================

export async function fetchTrackedApplications(status?: string, candidateId?: string): Promise<ApplicationTrackerItem[]> {
    try {
        const params = new URLSearchParams();
        if (status) params.append("status", status);
        if (candidateId) params.append("candidate_id", candidateId);
        const query = params.toString();
        const url = query ? `${GATEWAY_URL}/api/v1/tracker?${query}` : `${GATEWAY_URL}/api/v1/tracker`;
        const res = await fetch(url, { cache: "no-store" });
        if (res.ok) {
            return await res.json();
        }
        return [];
    } catch (err) {
        console.error("Error fetching tracked applications:", err);
        return [];
    }
}

export function buildTrackerId(candidateId: string, job: { id?: string | null; url?: string }): string {
    const rawKey = job.id || job.url || "job";
    const cleanKey = rawKey.replace(/[^a-zA-Z0-9_-]/g, "_");
    return `track_${candidateId}_${cleanKey}`;
}

export async function fetchTrackedApplication(trackerId: string, candidateId?: string): Promise<ApplicationTrackerItem | null> {
    try {
        const url = candidateId
            ? `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}?candidate_id=${encodeURIComponent(candidateId)}`
            : `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}`;
        const res = await fetch(url, { cache: "no-store" });
        if (res.ok) {
            return await res.json();
        }
        return null;
    } catch (err) {
        console.error("Error fetching single tracked application:", err);
        return null;
    }
}

export async function saveTrackedApplication(item: ApplicationTrackerItem): Promise<ApplicationTrackerItem | null> {
    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/tracker`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item),
        });
        if (res.ok) {
            return await res.json();
        }
        const errDetail = await res.text().catch(() => "");
        console.error(`Error saving tracked application HTTP ${res.status}:`, errDetail);
        return null;
    } catch (err) {
        console.error("Error saving tracked application:", err);
        return null;
    }
}

export async function updateTrackedStatus(trackerId: string, status: string, candidateId?: string): Promise<ApplicationTrackerItem | null> {
    try {
        const url = candidateId
            ? `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}/status?candidate_id=${encodeURIComponent(candidateId)}`
            : `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}/status`;
        const res = await fetch(url, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        if (res.ok) {
            return await res.json();
        }
        return null;
    } catch (err) {
        console.error("Error updating application status:", err);
        return null;
    }
}

export async function deleteTrackedApplication(trackerId: string, candidateId?: string): Promise<boolean> {
    try {
        const url = candidateId
            ? `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}?candidate_id=${encodeURIComponent(candidateId)}`
            : `${GATEWAY_URL}/api/v1/tracker/${encodeURIComponent(trackerId)}`;
        const res = await fetch(url, {
            method: "DELETE",
        });
        return res.ok;
    } catch (err) {
        console.error("Error deleting tracked application:", err);
        return false;
    }
}

// ==========================================
// Tailored Generator & Email Dispatch
// ==========================================

export async function generateApplicationMaterials(
    job: JobPosting,
    tone: string = "professional"
): Promise<ApplicationGenerateResponse | null> {
    try {
        const res = await fetch(`${GATEWAY_URL}/api/v1/generate/application`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job, custom_tone: tone }),
        });
        if (res.ok) {
            return await res.json();
        }
        return null;
    } catch (err) {
        console.error("Error generating application materials:", err);
        return null;
    }
}

export async function approveAndSendApplicationEmail(payload: {
    tracker_id: string;
    recipient_email: string;
    subject: string;
    body_text: string;
    approved: boolean;
}): Promise<{ status: string; message: string }> {
    const res = await fetch(`${GATEWAY_URL}/api/v1/email/approve-and-send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}: Failed to dispatch email`);
    }

    return await res.json();
}

export async function sendDailyDigest(minScore: number = 70): Promise<{ status: string; message: string }> {
    const res = await fetch(`${GATEWAY_URL}/api/v1/email/digest/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ min_score: minScore }),
    });

    if (!res.ok) {
        throw new Error(`Failed to send daily digest: HTTP ${res.status}`);
    }

    return await res.json();
}

export async function syncLinkedInAlerts(maxEmails: number = 25): Promise<LinkedInSyncResponse> {
    const res = await fetch(`${GATEWAY_URL}/api/v1/jobs/sync-linkedin-alerts?max_emails=${maxEmails}`, {
        method: "POST",
    });

    if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}: Failed to sync LinkedIn alerts`);
    }

    return await res.json();
}