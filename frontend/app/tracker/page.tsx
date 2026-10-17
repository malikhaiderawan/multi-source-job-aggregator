"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { ApplicationTrackerItem, JobPosting } from "@/types/job";
import {
    fetchTrackedApplications,
    updateTrackedStatus,
    deleteTrackedApplication,
    saveTrackedApplication,
    fetchActiveProfile
} from "@/lib/api-client";
import { ApplicationModal } from "@/components/ApplicationModal";

const STATUSES = [
    { key: "all", label: "All Items" },
    { key: "pending_approval", label: "Pending Approval" },
    { key: "applied", label: "Applied" },
    { key: "saved", label: "Saved / Bookmarked" },
    { key: "interview", label: "Interview" },
    { key: "follow_up", label: "Follow-up" },
    { key: "rejected", label: "Rejected" },
];

function parseJobMeta(title: string, company: string, location: string) {
    let cleanTitle = (title || "")
        .replace(/&middot;/gi, "·")
        .replace(/&amp;/gi, "&")
        .replace(/&quot;/gi, '"')
        .replace(/&#39;/gi, "'")
        .replace(/&nbsp;/gi, " ")
        .replace(/\s*Easy Apply\s*$/i, "")
        .trim();

    let cleanCompany = company;
    let cleanLocation = location;

    if (cleanTitle.includes("·")) {
        const parts = cleanTitle.split("·");
        const locPart = parts[1]?.trim() || "";
        const titleCompanyPart = parts[0]?.trim() || "";

        if (cleanLocation === "Unspecified Location" || !cleanLocation) {
            cleanLocation = locPart || cleanLocation;
        }

        cleanTitle = titleCompanyPart;
    }

    return { displayTitle: cleanTitle, displayCompany: cleanCompany, displayLocation: cleanLocation };
}

export default function TrackerPage() {
    const [activeFilter, setActiveFilter] = useState("all");
    const [allItems, setAllItems] = useState<ApplicationTrackerItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [candidateName, setCandidateName] = useState("Anser Nawaz");
    const [candidateId, setCandidateId] = useState("anser_nawaz");
    const [selectedModalData, setSelectedModalData] = useState<{
        job: JobPosting;
        initialTab?: "cv" | "letter" | "email";
    } | null>(null);

    const reloadData = useCallback(async (targetCandId?: string) => {
        const id = targetCandId || candidateId;
        setLoading(true);
        const data = await fetchTrackedApplications(undefined, id);
        setAllItems(data);
        setLoading(false);
    }, [candidateId]);

    useEffect(() => {
        let isMounted = true;
        fetchActiveProfile().then((prof) => {
            if (isMounted && prof) {
                setCandidateName(prof.profile.name);
                setCandidateId(prof.id);
                fetchTrackedApplications(undefined, prof.id).then((data) => {
                    if (isMounted) {
                        setAllItems(data);
                        setLoading(false);
                    }
                });
            } else if (isMounted) {
                fetchTrackedApplications().then((data) => {
                    if (isMounted) {
                        setAllItems(data);
                        setLoading(false);
                    }
                });
            }
        });
        return () => {
            isMounted = false;
        };
    }, []);

    const handleStatusUpdate = async (trackerId: string, newStatus: string) => {
        // Optimistic local update
        setAllItems((prev) =>
            prev.map((item) =>
                item.id === trackerId
                    ? {
                          ...item,
                          status: newStatus as ApplicationTrackerItem["status"],
                          job: { ...item.job, application_status: newStatus as ApplicationTrackerItem["status"] }
                      }
                    : item
            )
        );
        await updateTrackedStatus(trackerId, newStatus, candidateId);
        reloadData();
    };

    const handleDelete = async (trackerId: string) => {
        if (confirm("Remove this application from the tracker?")) {
            setAllItems((prev) => prev.filter((it) => it.id !== trackerId));
            await deleteTrackedApplication(trackerId, candidateId);
            reloadData();
        }
    };

    const handleNotesBlur = async (item: ApplicationTrackerItem, notes: string) => {
        item.notes = notes;
        await saveTrackedApplication(item);
    };

    // Calculate persistent counts across all statuses
    const statusCounts = useMemo(() => {
        return allItems.reduce((acc, it) => {
            acc[it.status] = (acc[it.status] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);
    }, [allItems]);

    // Client-side filtered items for 0ms tab switching
    const displayedItems = useMemo(() => {
        if (activeFilter === "all") return allItems;
        return allItems.filter((it) => it.status === activeFilter);
    }, [allItems, activeFilter]);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case "pending_approval":
                return {
                    label: "⏳ Pending Approval",
                    className: "bg-amber-100 text-amber-900 border-amber-300 font-bold",
                };
            case "applied":
                return {
                    label: "✓ Applied",
                    className: "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold",
                };
            case "interview":
                return {
                    label: "🎉 Interview",
                    className: "bg-purple-100 text-purple-900 border-purple-300 font-bold",
                };
            case "follow_up":
                return {
                    label: "📬 Follow-up",
                    className: "bg-indigo-100 text-indigo-900 border-indigo-300 font-bold",
                };
            case "rejected":
                return {
                    label: "✕ Rejected",
                    className: "bg-rose-100 text-rose-800 border-rose-300 font-semibold",
                };
            case "saved":
            default:
                return {
                    label: "📌 Bookmarked",
                    className: "bg-slate-100 text-slate-700 border-slate-300 font-semibold",
                };
        }
    };

    return (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                        Application Tracker & ATS
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                        Manage pipelines, review approval gates, and record interview stages for{" "}
                        <strong className="text-slate-800">{candidateName}</strong>.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2.5 py-1 bg-white text-slate-700 rounded-lg border border-slate-200 shadow-2xs">
                        {allItems.length} Tracked Roles
                    </span>
                    {statusCounts["pending_approval"] ? (
                        <span className="text-xs font-bold px-2.5 py-1 bg-amber-50 text-amber-800 rounded-lg border border-amber-300 shadow-2xs animate-pulse">
                            ⏳ {statusCounts["pending_approval"]} Awaiting Approval
                        </span>
                    ) : null}
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                {STATUSES.map((st) => {
                    const count = st.key === "all" ? allItems.length : statusCounts[st.key] || 0;
                    const isActive = activeFilter === st.key;
                    return (
                        <button
                            key={st.key}
                            onClick={() => setActiveFilter(st.key)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex items-center gap-1.5 cursor-pointer ${
                                isActive
                                    ? "bg-slate-900 text-white shadow-xs"
                                    : "bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200/90"
                            }`}
                        >
                            <span>{st.label}</span>
                            <span
                                className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                                    isActive
                                        ? "bg-white/20 text-white"
                                        : count > 0
                                        ? "bg-slate-100 text-slate-700"
                                        : "bg-slate-50 text-slate-400"
                                }`}
                            >
                                {count}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Application List */}
            {loading ? (
                <div className="space-y-3">
                    {[...Array(4)].map((_, i) => (
                        <div
                            key={i}
                            className="p-5 bg-white border border-slate-200/80 rounded-xl animate-pulse h-28"
                        />
                    ))}
                </div>
            ) : displayedItems.length > 0 ? (
                <div className="space-y-3.5">
                    {displayedItems.map((item) => {
                        const badge = getStatusBadge(item.status);
                        const { displayTitle, displayCompany, displayLocation } = parseJobMeta(item.job.title, item.job.company, item.job.location);
                        return (
                            <div
                                key={item.id}
                                className={`p-4 sm:p-5 bg-white border rounded-xl shadow-xs transition-all space-y-3 ${
                                    item.status === "pending_approval"
                                        ? "border-amber-300 ring-1 ring-amber-200/60"
                                        : item.status === "applied"
                                        ? "border-emerald-200 hover:border-emerald-300"
                                        : "border-slate-200/90 hover:border-slate-300"
                                }`}
                            >
                                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                                    <div className="flex-1 space-y-2">
                                        {/* Status & Category Badges */}
                                        <div className="flex items-center gap-1.5 flex-wrap">
                                            <span
                                                className={`text-[11px] px-2.5 py-0.5 rounded-md border ${badge.className}`}
                                            >
                                                {badge.label}
                                            </span>

                                            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                                                {item.job.match_score}% Match
                                            </span>

                                            {item.job.category && (
                                                <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-50 text-slate-600 border border-slate-200">
                                                    {item.job.category}
                                                </span>
                                            )}

                                            <span className="text-[11px] text-slate-400">
                                                Source: {item.job.source}
                                            </span>

                                            {/* Email Transmission Status Integrity */}
                                            {item.email_sent ? (
                                                <span className="text-[11px] font-bold px-2 py-0.5 bg-emerald-50 text-emerald-800 rounded border border-emerald-200">
                                                    ✉️ Email Transmitted (Live SMTP)
                                                </span>
                                            ) : (item.email_dispatch_mode === "simulated_dry_run" ||
                                                  (item.email_approved && !item.email_sent)) ? (
                                                <span className="text-[11px] font-semibold px-2 py-0.5 bg-amber-50 text-amber-800 rounded border border-amber-200">
                                                    📝 Dry-run Logged (Not Transmitted)
                                                </span>
                                            ) : null}
                                        </div>

                                        {/* Job Title & Details */}
                                        <div>
                                            <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedModalData({
                                                            job: item.job,
                                                            initialTab: item.status === "pending_approval" || item.status === "applied" ? "email" : "cv"
                                                        })
                                                    }
                                                    className="text-left font-bold text-slate-900 hover:text-blue-600 transition cursor-pointer inline-flex items-center gap-1.5 group"
                                                    title="Click to view tailored application materials & outreach pitch"
                                                >
                                                    <span>{displayTitle}</span>
                                                    <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 opacity-0 group-hover:opacity-100 transition shrink-0">
                                                        Tailor ✨
                                                    </span>
                                                </button>
                                            </h3>
                                            <p className="text-xs text-slate-500 font-medium mt-0.5">
                                                <strong className="text-slate-700">{displayCompany}</strong> — 📍{" "}
                                                {displayLocation} • 💳{" "}
                                                {item.job.salary || "Salary undisclosed"}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Action Controls & Status Selector */}
                                    <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap shrink-0">
                                        <div>
                                            <label className="sr-only">Change Status</label>
                                            <select
                                                value={item.status}
                                                onChange={(e) => handleStatusUpdate(item.id, e.target.value)}
                                                className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold bg-white text-slate-800 shadow-2xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none cursor-pointer"
                                            >
                                                <option value="pending_approval">⏳ Pending Approval</option>
                                                <option value="applied">✓ Applied</option>
                                                <option value="saved">📌 Saved</option>
                                                <option value="interview">🎉 Interview</option>
                                                <option value="follow_up">📬 Follow-up</option>
                                                <option value="rejected">✕ Rejected</option>
                                            </select>
                                        </div>

                                        {item.status === "applied" ? (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={() => handleStatusUpdate(item.id, "interview")}
                                                    className="px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1.5 active:scale-95"
                                                    title="Recruiter called or emailed for an interview? Click to progress to Interview stage!"
                                                >
                                                    <span>🎉 Got Interview?</span>
                                                </button>

                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedModalData({
                                                            job: item.job,
                                                            initialTab: "email"
                                                        })
                                                    }
                                                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs cursor-pointer whitespace-nowrap"
                                                    title="Review submitted pitch, cover letter, and tailored CV"
                                                >
                                                    Submitted Pitch
                                                </button>

                                                <a
                                                    href={item.job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1"
                                                    title="View original job posting"
                                                >
                                                    <span>Job Link</span>
                                                    <svg className="w-3 h-3 text-slate-400" viewBox="0 0 16 16" fill="none">
                                                        <path
                                                            d="M4 12L12 4H6M12 4V10"
                                                            stroke="currentColor"
                                                            strokeWidth="1.3"
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                        />
                                                    </svg>
                                                </a>
                                            </>
                                        ) : item.status === "pending_approval" ? (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedModalData({
                                                            job: item.job,
                                                            initialTab: "email"
                                                        })
                                                    }
                                                    className="px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1.5 active:scale-95"
                                                    title="Review drafted email outreach and approve sending"
                                                >
                                                    <span>Review & Send Email →</span>
                                                </button>

                                                <a
                                                    href={item.job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1"
                                                    title="View original job posting"
                                                >
                                                    <span>Job Link</span>
                                                    <svg className="w-3 h-3 text-slate-400" viewBox="0 0 16 16" fill="none">
                                                        <path
                                                            d="M4 12L12 4M12 4H6M12 4V10"
                                                            stroke="currentColor"
                                                            strokeWidth="1.3"
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                        />
                                                    </svg>
                                                </a>
                                            </>
                                        ) : item.status === "interview" ? (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedModalData({
                                                            job: item.job,
                                                            initialTab: "cv"
                                                        })
                                                    }
                                                    className="px-3 py-1.5 text-xs font-bold rounded-lg bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1"
                                                    title="Review tailored CV talking points & interview pitch"
                                                >
                                                    <span>CV Highlights</span>
                                                </button>

                                                <a
                                                    href={item.job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1"
                                                    title="View original job posting"
                                                >
                                                    <span>Job Link</span>
                                                    <svg className="w-3 h-3 text-slate-400" viewBox="0 0 16 16" fill="none">
                                                        <path
                                                            d="M4 12L12 4M12 4H6M12 4V10"
                                                            stroke="currentColor"
                                                            strokeWidth="1.3"
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                        />
                                                    </svg>
                                                </a>
                                            </>
                                        ) : (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedModalData({
                                                            job: item.job,
                                                            initialTab: "cv"
                                                        })
                                                    }
                                                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs cursor-pointer whitespace-nowrap"
                                                    title="View and edit tailored CV bullets, cover letter, and outreach pitch"
                                                >
                                                    Tailor Pitch
                                                </button>

                                                <a
                                                    href={item.job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-800 transition shadow-2xs whitespace-nowrap cursor-pointer flex items-center gap-1"
                                                    title="Open official career portal in a new tab"
                                                >
                                                    <span>Apply Official</span>
                                                    <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none">
                                                        <path
                                                            d="M4 12L12 4M12 4H6M12 4V10"
                                                            stroke="currentColor"
                                                            strokeWidth="1.5"
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                        />
                                                    </svg>
                                                </a>
                                            </>
                                        )}

                                        <button
                                            type="button"
                                            onClick={() => handleDelete(item.id)}
                                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition cursor-pointer"
                                            title="Delete from tracker"
                                        >
                                            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
                                                <path
                                                    d="M3 4H13M5.5 4V2.5H10.5V4M6.5 7V11M9.5 7V11M4 4L4.8 13.5H11.2L12 4"
                                                    stroke="currentColor"
                                                    strokeWidth="1.3"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                />
                                            </svg>
                                        </button>
                                    </div>
                                </div>

                                {/* Special Interactive Banner for Pending Approval */}
                                {item.status === "pending_approval" && (
                                    <div className="bg-amber-50/80 border border-amber-200/90 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                                        <div className="flex items-start sm:items-center gap-2.5">
                                            <span className="text-lg shrink-0">⏳</span>
                                            <div>
                                                <p className="font-bold text-amber-950">
                                                    Awaiting Human Approval Gate
                                                </p>
                                                <p className="text-amber-800 text-[11px] mt-0.5 leading-relaxed">
                                                    Tailored pitch drafted. Review recruiter email, verify the approval checkbox, and click Send Approved Email to transmit with attached resume.
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setSelectedModalData({
                                                    job: item.job,
                                                    initialTab: "email"
                                                })
                                            }
                                            className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg transition shadow-xs whitespace-nowrap cursor-pointer text-xs shrink-0 flex items-center gap-1.5 self-start sm:self-auto"
                                        >
                                            <span>Review & Approve Email</span>
                                            <span>→</span>
                                        </button>
                                    </div>
                                )}

                                {/* Private Candidate Note */}
                                <div>
                                    <input
                                        type="text"
                                        defaultValue={item.notes || ""}
                                        onBlur={(e) => handleNotesBlur(item, e.target.value)}
                                        placeholder="Add private note (e.g. recruiter contacted, interview scheduled, salary expectation)..."
                                        className="w-full text-xs px-3 py-1.5 border border-slate-200 rounded-lg bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="text-center py-16 border border-dashed border-slate-300 rounded-xl bg-white p-6 space-y-2">
                    <p className="text-sm font-semibold text-slate-800">
                        No applications found in &quot;{STATUSES.find((s) => s.key === activeFilter)?.label}&quot;
                    </p>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto">
                        Save positions from the Discover feed or generate customized materials to track them here.
                    </p>
                </div>
            )}

            {/* Modal */}
            {selectedModalData && (
                <ApplicationModal
                    job={selectedModalData.job}
                    initialTab={selectedModalData.initialTab}
                    onClose={() => setSelectedModalData(null)}
                    onStatusChange={() => reloadData()}
                />
            )}
        </main>
    );
}
