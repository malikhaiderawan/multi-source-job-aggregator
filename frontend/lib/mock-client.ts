import { JobPosting, JobListResponse, JobQuery } from "@/types/job";

const MOCK_JOBS: JobPosting[] = [
    {
        id: "1",
        title: "Senior React Native & Mobile Engineer",
        company: "Mobile Systems Inc",
        location: "Lahore, Pakistan (Hybrid / Remote)",
        salary: "$70,000 - $95,000",
        url: "https://example.com/job/1",
        source: "Jooble",
        match_score: 95,
        category: "Mobile",
        seniority_level: "Senior Engineer",
        tags: ["React Native", "Flutter", "iOS", "Android"],
        is_remote: true,
        description_snippet: "Leading development of cross-platform apps using React Native and Flutter."
    },
    {
        id: "2",
        title: "Senior Full Stack Engineer (Next.js & Node.js)",
        company: "SaaS Scale GmbH",
        location: "Worldwide Remote",
        salary: "$90,000 - $120,000",
        url: "https://example.com/job/2",
        source: "Remotive",
        match_score: 92,
        category: "Full-stack",
        seniority_level: "Senior Engineer",
        tags: ["Next.js", "React", "Node.js", "TypeScript"],
        is_remote: true,
        description_snippet: "High-scale SaaS platform looking for a Senior Full Stack Engineer with 5+ years experience."
    },
];

export async function fetchMockJobs(query: JobQuery): Promise<JobListResponse> {
    // Simulate network latency
    await new Promise((resolve) => setTimeout(resolve, 300));

    const kw = query.keyword?.toLowerCase() || "";
    const loc = query.location?.toLowerCase() || "";

    const filtered = MOCK_JOBS.filter(
        (job) =>
            (!kw || job.title.toLowerCase().includes(kw) || job.company.toLowerCase().includes(kw)) &&
            (!loc || job.location.toLowerCase().includes(loc))
    );

    return {
        total_count: filtered.length,
        count: filtered.length,
        results: filtered,
    };
}