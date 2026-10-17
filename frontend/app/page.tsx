"use client";

import { useState, useEffect } from "react";
import { fetchLiveJobs, fetchActiveProfile, syncLinkedInAlerts, fetchTrackedApplications } from "@/lib/api-client";
import { JobPosting, CandidateProfileMeta, LinkedInSyncResponse } from "@/types/job";
import { JobCard } from "@/components/JobCard";

const CATEGORIES = [
    { id: "All", label: "All Opportunities" },
    { id: "Mobile", label: "Mobile (React Native / Flutter)" },
    { id: "Frontend", label: "Frontend (React / Next.js)" },
    { id: "Backend", label: "Backend (Node.js / Python)" },
    { id: "Full-stack", label: "Full-Stack & Lead" },
];

const LOCATION_PRESETS = [
    { label: "All Locations", value: "" },
    { label: "📍 Lahore", value: "Lahore" },
    { label: "🇵🇰 Pakistan", value: "Pakistan" },
    { label: "🌐 Remote", value: "Remote" },
];

const ELIGIBILITY_OPTIONS = [
    { id: "all", label: "All Regions" },
    { id: "lahore_local", label: "📍 Lahore On-site / Hybrid" },
    { id: "pakistan_all", label: "🇵🇰 Pakistan (Local & Remote)" },
    { id: "worldwide_remote", label: "🌐 Worldwide Remote (Pakistan OK)" },
    { id: "eligibility_unknown", label: "❓ Unconfirmed Remote" },
];

export default function HomePage() {
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [category, setCategory] = useState("All");
    const [eligibility, setEligibility] = useState("all");
    const [minScore, setMinScore] = useState(0);
    const [providerFilter, setProviderFilter] = useState("all");

    const [activeCandidate, setActiveCandidate] = useState<CandidateProfileMeta | null>(null);
    const [jobs, setJobs] = useState<JobPosting[]>([]);
    const [totalCount, setTotalCount] = useState<number>(0);
    const [lastFetched, setLastFetched] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [statusMessage, setStatusMessage] = useState("Loading scored jobs...");
    const [categoriesCount, setCategoriesCount] = useState<Record<string, number>>({});
    const [providersCount, setProvidersCount] = useState<Record<string, number>>({});
    const [eligibilityCount, setEligibilityCount] = useState<Record<string, number>>({});
    const [trackedCount, setTrackedCount] = useState<number>(0);

    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<LinkedInSyncResponse | null>(null);
    const [syncModalOpen, setSyncModalOpen] = useState(false);

    useEffect(() => {
        let isMounted = true;
        fetchActiveProfile().then((data) => {
            if (isMounted && data) {
                setActiveCandidate(data);
                fetchTrackedApplications(undefined, data.id).then((tracked) => {
                    if (isMounted) setTrackedCount(tracked.length);
                });
            }
        });

        fetchLiveJobs({
            keyword,
            location,
            category,
            eligibility,
            minScore,
            limit: 100,
        }).then((data) => {
            if (isMounted) {
                setJobs(data.results);
                setTotalCount(data.total_count || 0);
                setLastFetched(data.query_timestamp || new Date().toISOString());
                setCategoriesCount(data.categories_count || {});
                setProvidersCount(data.providers_count || {});
                setEligibilityCount(data.eligibility_count || {});
                setStatusMessage(`Loaded ${data.total_count || data.count} scored positions.`);
                setLoading(false);
            }
        }).catch(() => {
            if (isMounted) {
                setStatusMessage("Gateway unreachable. Please verify backend is running on port 8000.");
                setLoading(false);
            }
        });

        return () => {
            isMounted = false;
        };
    }, [category, eligibility, minScore, location, keyword]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setStatusMessage("Fetching scored opportunities...");
        fetchLiveJobs({
            keyword,
            location,
            category,
            eligibility,
            minScore,
            limit: 100,
        }).then((data) => {
            setJobs(data.results);
            setTotalCount(data.total_count || 0);
            setLastFetched(data.query_timestamp || new Date().toISOString());
            setCategoriesCount(data.categories_count || {});
            setProvidersCount(data.providers_count || {});
            setEligibilityCount(data.eligibility_count || {});
            setStatusMessage(`Loaded ${data.total_count || data.count} scored positions.`);
            setLoading(false);
        }).catch(() => {
            setStatusMessage("Gateway error. Check backend logs.");
            setLoading(false);
        });
    };

    const handleResetFilters = () => {
        setKeyword("");
        setLocation("");
        setCategory("All");
        setEligibility("all");
        setMinScore(0);
        setProviderFilter("all");
    };

    const hasActiveFilters =
        keyword.trim() !== "" ||
        location.trim() !== "" ||
        category !== "All" ||
        eligibility !== "all" ||
        minScore > 0 ||
        providerFilter !== "all";

    const handleSyncAlerts = async () => {
        setSyncing(true);
        try {
            const res = await syncLinkedInAlerts(25);
            setSyncResult(res);
            setSyncModalOpen(true);
            if (res.unique_jobs_added > 0 || res.jobs_extracted > 0) {
                fetchLiveJobs({
                    keyword,
                    location,
                    category,
                    eligibility,
                    minScore,
                    limit: 100,
                }).then((data) => {
                    setJobs(data.results);
                    setTotalCount(data.total_count || 0);
                    setLastFetched(data.query_timestamp || new Date().toISOString());
                    setCategoriesCount(data.categories_count || {});
                    setProvidersCount(data.providers_count || {});
                    setEligibilityCount(data.eligibility_count || {});
                });
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to sync LinkedIn alert emails.";
            setSyncResult({
                status: "error",
                message: msg,
                emails_scanned: 0,
                jobs_extracted: 0,
                unique_jobs_added: 0,
                duplicates_skipped: 0,
                failures: 1,
                eligibility_count: {},
                jobs: []
            });
            setSyncModalOpen(true);
        } finally {
            setSyncing(false);
        }
    };

    const handleRefreshJobs = () => {
        setLoading(true);
        setStatusMessage("Refreshing all provider feeds...");
        fetchLiveJobs({
            keyword,
            location,
            category,
            eligibility,
            minScore,
            limit: 100,
        }).then((data) => {
            setJobs(data.results);
            setTotalCount(data.total_count || 0);
            setLastFetched(data.query_timestamp || new Date().toISOString());
            setCategoriesCount(data.categories_count || {});
            setProvidersCount(data.providers_count || {});
            setEligibilityCount(data.eligibility_count || {});
            setStatusMessage(`Refreshed — ${data.total_count || data.count} positions loaded.`);
            setLoading(false);
        }).catch(() => {
            setStatusMessage("Refresh failed. Check backend connection.");
            setLoading(false);
        });
    };

    const formatTimestamp = (iso: string) => {
        if (!iso) return "";
        try {
            const d = new Date(iso);
            return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        } catch {
            return "";
        }
    };

    const displayedJobs = jobs.filter((job) =>
        providerFilter === "all" ? true : job.source.toLowerCase() === providerFilter.toLowerCase()
    );

    const candidateName = activeCandidate?.profile.name || "Anser Nawaz";
    const candidateExp = activeCandidate?.profile.total_years_experience || 6;
    const candidateHeadline = activeCandidate?.profile.headline || "Senior Full-Stack & Mobile Engineer | Team Lead";
    const candidateSkills = activeCandidate?.profile.all_skills || [
        "React Native",
        "Flutter",
        "React.js",
        "Next.js",
        "Node.js",
        "FastAPI",
        "PostgreSQL"
    ];

    const lahoreTotal = (eligibilityCount["lahore_onsite"] || 0) + (eligibilityCount["lahore_hybrid"] || 0);
    const pakRemoteTotal = eligibilityCount["pakistan_remote"] || 0;
    const worldwideTotal = eligibilityCount["worldwide_remote"] || 0;

    return (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
            {/* Candidate Header Brief: Modern Executive Surface */}
            <div className="bg-white border border-slate-200/90 rounded-xl p-5 sm:p-6 shadow-xs relative overflow-hidden">
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-5">
                    <div className="space-y-2 max-w-3xl">
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                                Active Candidate
                            </span>
                            <span className="text-xs text-slate-500 font-medium">
                                Scoring aligned for <strong className="text-slate-800">{candidateName}</strong> ({candidateExp}+ Years Experience)
                            </span>
                        </div>

                        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight leading-snug">
                            {candidateHeadline}
                        </h1>

                        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                            Discovering, deduplicating, and scoring opportunities from <strong>LinkedIn Alerts</strong>, <strong>Jooble</strong>, <strong>Remotive</strong>, <strong>Jobicy</strong>, <strong>Arbeitnow</strong>, and <strong>WeWorkRemotely</strong> across Lahore, Pakistan, and International Remote hubs.
                        </p>

                        <div className="flex items-center gap-1.5 flex-wrap pt-1">
                            {candidateSkills.slice(0, 7).map((skill) => (
                                <span
                                    key={skill}
                                    className="text-[11px] font-medium px-2 py-0.5 bg-slate-50 text-slate-700 rounded-md border border-slate-200"
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col sm:flex-row lg:flex-col items-start lg:items-end gap-2 shrink-0 pt-2 lg:pt-0">
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={handleRefreshJobs}
                                disabled={loading}
                                className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer focus:outline-none focus:ring-2 focus:ring-slate-900/20 whitespace-nowrap"
                            >
                                <svg
                                    className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
                                    viewBox="0 0 16 16"
                                    fill="none"
                                >
                                    <path
                                        d="M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2M14 2V6M14 6H10"
                                        stroke="currentColor"
                                        strokeWidth="1.5"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                                <span>{loading ? "Refreshing..." : "Refresh Jobs"}</span>
                            </button>
                            <button
                                type="button"
                                onClick={handleSyncAlerts}
                                disabled={syncing}
                                className="inline-flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20 whitespace-nowrap"
                            >
                                <svg className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} viewBox="0 0 16 16" fill="none">
                                    <path d="M2.5 4.5H13.5V11.5H2.5V4.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
                                    <path d="M2.5 5L8 8.5L13.5 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                                <span>{syncing ? "Scanning..." : "Sync Emails"}</span>
                            </button>
                        </div>
                        <span className="text-[11px] text-slate-400 font-medium">
                            {lastFetched ? `Last fetched ${formatTimestamp(lastFetched)}` : "Fetches live from all providers"}
                        </span>
                    </div>
                </div>
            </div>

            {/* Dashboard Overview: Clean Key Metrics Row */}
            <div className="bg-white border border-slate-200/90 rounded-xl shadow-xs overflow-hidden">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
                    <div className="p-4 sm:p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                            Total Positions
                        </p>
                        <p className="text-xl sm:text-2xl font-bold text-slate-900 mt-1 tracking-tight">
                            {totalCount}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Matching criteria</p>
                    </div>

                    <div className="p-4 sm:p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
                            Lahore Local
                        </p>
                        <p className="text-xl sm:text-2xl font-bold text-emerald-700 mt-1 tracking-tight">
                            {lahoreTotal}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">On-site & Hybrid</p>
                    </div>

                    <div className="p-4 sm:p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-green-700">
                            Pakistan Remote
                        </p>
                        <p className="text-xl sm:text-2xl font-bold text-green-700 mt-1 tracking-tight">
                            {pakRemoteTotal}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Country-wide remote</p>
                    </div>

                    <div className="p-4 sm:p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-700">
                            Worldwide Remote
                        </p>
                        <p className="text-xl sm:text-2xl font-bold text-sky-700 mt-1 tracking-tight">
                            {worldwideTotal}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Pakistan-eligible</p>
                    </div>

                    <div className="p-4 sm:p-5 col-span-2 sm:col-span-1">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-blue-700">
                            Tracked In ATS
                        </p>
                        <p className="text-xl sm:text-2xl font-bold text-blue-700 mt-1 tracking-tight">
                            {trackedCount}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Applications & saves</p>
                    </div>
                </div>
            </div>

            {/* Category Quick Filter Pills */}
            <div className="space-y-2">
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                    {CATEGORIES.map((cat) => {
                        const isSelected = category === cat.id;
                        const count = categoriesCount[cat.id];
                        return (
                            <button
                                key={cat.id}
                                type="button"
                                onClick={() => setCategory(cat.id)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
                                    isSelected
                                        ? "bg-slate-900 text-white shadow-xs"
                                        : "bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200/90"
                                }`}
                            >
                                <span>{cat.label}</span>
                                {count !== undefined && count > 0 && (
                                    <span
                                        className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                                            isSelected ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600"
                                        }`}
                                    >
                                        {count}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* Location Eligibility Filter Pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 whitespace-nowrap mr-1">
                        Eligibility:
                    </span>
                    {ELIGIBILITY_OPTIONS.map((elig) => {
                        const isSelected = eligibility === elig.id;
                        return (
                            <button
                                key={elig.id}
                                type="button"
                                onClick={() => setEligibility(elig.id)}
                                className={`px-2.5 py-1 rounded-md text-xs font-medium transition whitespace-nowrap cursor-pointer ${
                                    isSelected
                                        ? "bg-blue-50 text-blue-700 border border-blue-300 font-semibold shadow-2xs"
                                        : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
                                }`}
                            >
                                {elig.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Search and Filters Card */}
            <form
                onSubmit={handleSearch}
                className="bg-white rounded-xl border border-slate-200/90 p-4 sm:p-5 shadow-xs space-y-4"
            >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3.5">
                    {/* Keyword Input */}
                    <div className="lg:col-span-4">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Keywords / Skills
                        </label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                    <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
                                    <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                            </span>
                            <input
                                type="text"
                                value={keyword}
                                onChange={(e) => setKeyword(e.target.value)}
                                placeholder="e.g. Flutter, React, Node.js, Next.js"
                                className="w-full pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
                            />
                        </div>
                    </div>

                    {/* Location Input */}
                    <div className="lg:col-span-3">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Location
                        </label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                    <path
                                        d="M8 1.5C5.51472 1.5 3.5 3.51472 3.5 6C3.5 9.5 8 14.5 8 14.5C8 14.5 12.5 9.5 12.5 6C12.5 3.51472 10.4853 1.5 8 1.5Z"
                                        stroke="currentColor"
                                        strokeWidth="1.3"
                                    />
                                    <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.3" />
                                </svg>
                            </span>
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="e.g. Lahore, Pakistan, Remote"
                                className="w-full pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
                            />
                        </div>
                    </div>

                    {/* Min Match Score */}
                    <div className="lg:col-span-2">
                        <div className="flex items-center justify-between mb-1">
                            <label className="text-xs font-semibold text-slate-700">
                                Min Match
                            </label>
                            <span className="text-xs font-semibold text-blue-600">
                                {minScore}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="90"
                            step="10"
                            value={minScore}
                            onChange={(e) => setMinScore(Number(e.target.value))}
                            className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg mt-1"
                        />
                    </div>

                    {/* Source Provider Dropdown */}
                    <div className="lg:col-span-2">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Provider
                        </label>
                        <select
                            value={providerFilter}
                            onChange={(e) => setProviderFilter(e.target.value)}
                            className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
                        >
                            <option value="all">All Sources</option>
                            <option value="linkedin alert">LinkedIn Alert</option>
                            <option value="indeed alert">Indeed Alert</option>
                            <option value="mustakbil (pakistan)">Mustakbil (Pakistan)</option>
                            <option value="remotive">Remotive</option>
                            <option value="jobicy">Jobicy</option>
                            <option value="arbeitnow">Arbeitnow</option>
                            <option value="weworkremotely">WeWorkRemotely</option>
                            <option value="jooble">Jooble</option>
                        </select>
                    </div>

                    {/* Search Submit Button */}
                    <div className="lg:col-span-1 flex items-end">
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-1.5 px-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition shadow-xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-slate-900/20 flex items-center justify-center gap-1.5 h-[34px]"
                        >
                            {loading ? "..." : "Filter"}
                        </button>
                    </div>
                </div>

                {/* Sub-row: Quick location presets & Reset action */}
                <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                            Quick:
                        </span>
                        {LOCATION_PRESETS.map((p) => {
                            const active = location.toLowerCase() === p.value.toLowerCase();
                            return (
                                <button
                                    type="button"
                                    key={p.label}
                                    onClick={() => setLocation(p.value)}
                                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition cursor-pointer ${
                                        active
                                            ? "bg-blue-50 text-blue-700 border border-blue-200 font-semibold"
                                            : "bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200"
                                    }`}
                                >
                                    {p.label}
                                </button>
                            );
                        })}
                    </div>

                    {hasActiveFilters && (
                        <button
                            type="button"
                            onClick={handleResetFilters}
                            className="text-xs text-slate-500 hover:text-slate-800 font-medium underline flex items-center gap-1 cursor-pointer"
                        >
                            <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none">
                                <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            </svg>
                            <span>Clear all filters</span>
                        </button>
                    )}
                </div>
            </form>

            {/* Results Header / Live Status */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600">
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${loading ? "bg-amber-500 animate-ping" : "bg-emerald-500"}`} />
                    <span className="font-medium text-slate-700">{statusMessage}</span>
                </div>

                {!loading && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                        {Object.entries(providersCount).map(([src, count]) => (
                            <span
                                key={src}
                                className="text-[10px] font-medium px-2 py-0.5 bg-white border border-slate-200 rounded text-slate-600"
                            >
                                {src}: <strong className="text-slate-900">{count}</strong>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Job Listings Grid */}
            {loading ? (
                <div className="grid gap-3.5 grid-cols-1 md:grid-cols-2">
                    {[...Array(6)].map((_, i) => (
                        <div
                            key={i}
                            className="p-5 border border-slate-200/80 rounded-xl bg-white animate-pulse h-44 flex flex-col justify-between"
                        >
                            <div className="space-y-2.5">
                                <div className="h-4 bg-slate-100 rounded w-1/3" />
                                <div className="h-5 bg-slate-100 rounded w-3/4" />
                                <div className="h-3 bg-slate-100 rounded w-1/2" />
                            </div>
                            <div className="h-4 bg-slate-100 rounded w-1/4" />
                        </div>
                    ))}
                </div>
            ) : displayedJobs.length > 0 ? (
                <div className="grid gap-3.5 grid-cols-1 md:grid-cols-2">
                    {displayedJobs.map((job) => (
                        <JobCard
                            key={job.id || job.url}
                            job={job}
                            candidateId={activeCandidate?.id || "anser_nawaz"}
                            onStatusChange={() => {
                                fetchTrackedApplications(undefined, activeCandidate?.id).then((tracked) => {
                                    setTrackedCount(tracked.length);
                                });
                            }}
                        />
                    ))}
                </div>
            ) : (
                <div className="text-center py-16 border border-dashed border-slate-300 rounded-xl bg-white p-6 space-y-3">
                    <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                        <svg className="w-5 h-5" viewBox="0 0 16 16" fill="none">
                            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
                            <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-slate-800">
                            No opportunities match your current criteria
                        </p>
                        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                            Try adjusting your minimum match threshold, switching region filters, or clearing specific keyword filters.
                        </p>
                    </div>
                    {hasActiveFilters && (
                        <button
                            type="button"
                            onClick={handleResetFilters}
                            className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition"
                        >
                            Reset all filters
                        </button>
                    )}
                </div>
            )}

            {/* LinkedIn Job Alert Ingestion Sync Modal */}
            {syncModalOpen && syncResult && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
                    <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150 space-y-4">
                        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                            <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-md bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-200/60 font-semibold text-xs">
                                    IN
                                </div>
                                <h2 className="text-sm font-bold text-slate-900">
                                    LinkedIn Job Alert Email Sync
                                </h2>
                            </div>
                            <button
                                type="button"
                                onClick={() => setSyncModalOpen(false)}
                                className="text-slate-400 hover:text-slate-600 p-1 rounded-md text-base font-bold transition"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="space-y-4">
                            {syncResult.status === "missing_credentials" ? (
                                <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 space-y-2.5">
                                    <div className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
                                        <span>⚠️ Mailbox Credentials Required</span>
                                    </div>
                                    <p className="text-xs text-amber-800 leading-relaxed">
                                        {syncResult.message}
                                    </p>
                                    <div className="p-3 bg-amber-100/70 rounded-md text-[11px] font-mono text-amber-950 space-y-0.5">
                                        <div># In your .env file:</div>
                                        <div>LINKEDIN_ALERT_EMAIL_USER=your_email@gmail.com</div>
                                        <div>LINKEDIN_ALERT_EMAIL_PASS=your_app_password</div>
                                        <div>LINKEDIN_ALERT_IMAP_SERVER=imap.gmail.com</div>
                                        <div>LINKEDIN_ALERT_IMAP_PORT=993</div>
                                    </div>
                                </div>
                            ) : syncResult.status === "error" ? (
                                <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 space-y-1.5">
                                    <div className="text-xs font-semibold text-rose-900">
                                        Mailbox Sync Error
                                    </div>
                                    <p className="text-xs text-rose-800 font-mono leading-relaxed">
                                        {syncResult.message}
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                                        <p className="text-xs font-medium text-emerald-900">
                                            {syncResult.message}
                                        </p>
                                    </div>

                                    {/* Metrics Grid */}
                                    <div className="grid grid-cols-2 gap-2.5 text-center">
                                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                                            <div className="text-lg font-bold text-slate-900">
                                                {syncResult.emails_scanned}
                                            </div>
                                            <div className="text-[11px] text-slate-500 font-medium">
                                                Emails Scanned
                                            </div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                                            <div className="text-lg font-bold text-slate-900">
                                                {syncResult.jobs_extracted}
                                            </div>
                                            <div className="text-[11px] text-slate-500 font-medium">
                                                Jobs Extracted
                                            </div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
                                            <div className="text-lg font-bold text-blue-700">
                                                {syncResult.unique_jobs_added}
                                            </div>
                                            <div className="text-[11px] text-blue-700 font-semibold">
                                                New Unique Added
                                            </div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                                            <div className="text-lg font-bold text-slate-700">
                                                {syncResult.duplicates_skipped}
                                            </div>
                                            <div className="text-[11px] text-slate-500 font-medium">
                                                Duplicates Skipped
                                            </div>
                                        </div>
                                    </div>

                                    {/* Regional eligibility breakdown */}
                                    {Object.keys(syncResult.eligibility_count).length > 0 && (
                                        <div className="space-y-1.5 pt-2 border-t border-slate-100">
                                            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                                                Regional Eligibility Breakdown:
                                            </div>
                                            <div className="flex items-center gap-1.5 flex-wrap">
                                                {Object.entries(syncResult.eligibility_count).map(([elig, cnt]) => (
                                                    <span
                                                        key={elig}
                                                        className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200"
                                                    >
                                                        {elig.replace("_", " ")}: {cnt}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="pt-3 border-t border-slate-100 flex justify-end">
                            <button
                                type="button"
                                onClick={() => setSyncModalOpen(false)}
                                className="px-3.5 py-1.5 text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white rounded-lg transition"
                            >
                                Done
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}