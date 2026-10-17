"use client";

import { useState } from "react";
import { JobPosting } from "@/types/job";
import { ApplicationModal } from "./ApplicationModal";
import { saveTrackedApplication, deleteTrackedApplication, buildTrackerId } from "@/lib/api-client";

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

export function JobCard({
    job,
    candidateId = "anser_nawaz",
    onStatusChange
}: {
    job: JobPosting;
    candidateId?: string;
    onStatusChange?: (newStatus: string) => void;
}) {
    const [modalOpen, setModalOpen] = useState(false);
    const [currentStatus, setCurrentStatus] = useState(job.application_status || "untracked");
    const [isSaving, setIsSaving] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState("");

    const { displayTitle, displayCompany, displayLocation } = parseJobMeta(job.title, job.company, job.location);

    const handleMarkApplied = async (e?: React.MouseEvent, autoFromExternalLink: boolean = false) => {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        if (currentStatus === "applied" && !autoFromExternalLink) {
            return;
        }

        setIsSaving(true);
        setCurrentStatus("applied");
        setFeedbackMsg(autoFromExternalLink ? "Applied ✓" : "Marked Applied ✓");
        setTimeout(() => setFeedbackMsg(""), 3500);

        try {
            const trackerId = buildTrackerId(candidateId, job);
            await saveTrackedApplication({
                id: trackerId,
                candidate_id: candidateId,
                job: { ...job, application_status: "applied" },
                status: "applied",
                tailored_cv_bullet_points: [],
                tailored_cover_letter: "",
                tailored_recruiter_email: "",
                email_recipient: job.contact_email || "",
                email_approved: false
            });
            if (onStatusChange) onStatusChange("applied");
        } catch (err) {
            console.error("Failed to mark job applied:", err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleUnmarkApplied = async (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();

        setIsSaving(true);
        setCurrentStatus("untracked");
        setFeedbackMsg("Status cleared");
        setTimeout(() => setFeedbackMsg(""), 2000);

        try {
            const trackerId = buildTrackerId(candidateId, job);
            await deleteTrackedApplication(trackerId, candidateId);
            if (onStatusChange) onStatusChange("untracked");
        } catch (err) {
            console.error("Failed to clear application status:", err);
        } finally {
            setIsSaving(false);
        }
    };

    const getScoreBadgeColor = (score: number) => {
        if (score >= 85) return "bg-emerald-50 text-emerald-700 border-emerald-200";
        if (score >= 70) return "bg-blue-50 text-blue-700 border-blue-200";
        return "bg-slate-50 text-slate-700 border-slate-200";
    };

    const getEligibilityBadge = (eligibility?: string) => {
        switch (eligibility) {
            case "lahore_onsite":
                return {
                    label: "📍 Lahore On-site",
                    className: "bg-emerald-50 text-emerald-700 border-emerald-200/90",
                    isEligible: true
                };
            case "lahore_hybrid":
                return {
                    label: "🏢 Lahore Hybrid",
                    className: "bg-teal-50 text-teal-700 border-teal-200/90",
                    isEligible: true
                };
            case "pakistan_remote":
                return {
                    label: "🇵🇰 Pakistan Remote",
                    className: "bg-green-50 text-green-700 border-green-200/90",
                    isEligible: true
                };
            case "worldwide_remote":
                return {
                    label: "🌐 Worldwide Remote",
                    className: "bg-sky-50 text-sky-700 border-sky-200/90",
                    isEligible: true
                };
            case "ineligible_region":
                return {
                    label: "🚫 Region Restricted",
                    className: "bg-rose-50 text-rose-700 border-rose-200/90",
                    isEligible: false
                };
            case "pakistan_onsite":
                return {
                    label: "🏢 Non-Lahore On-site",
                    className: "bg-purple-50 text-purple-700 border-purple-200/90",
                    isEligible: false
                };
            case "pakistan_hybrid":
                return {
                    label: "🏢 Non-Lahore Hybrid",
                    className: "bg-indigo-50 text-indigo-700 border-indigo-200/90",
                    isEligible: false
                };
            case "eligibility_unknown":
            default:
                return {
                    label: "❓ Eligibility Unconfirmed",
                    className: "bg-amber-50 text-amber-700 border-amber-200/90",
                    isEligible: false
                };
        }
    };

    const hasSalary =
        job.salary &&
        !["not specified", "unspecified"].includes(job.salary.toLowerCase()) &&
        job.salary.trim() !== "";

    const eligBadge = getEligibilityBadge(job.location_eligibility);

    return (
        <>
            <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all duration-150 flex flex-col justify-between space-y-3.5 group">
                <div className="space-y-2.5">
                    {/* Top Row: Score + Eligibility Badge + Category + Source */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                                className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${getScoreBadgeColor(
                                    job.match_score
                                )}`}
                                title={`Match score: ${job.match_score}% based on candidate skills`}
                            >
                                {job.match_score}% Match
                            </span>

                            <span
                                className={`text-[10px] font-medium px-2 py-0.5 rounded-md border ${eligBadge.className}`}
                                title={job.eligibility_detail || "Regional location verification"}
                            >
                                {eligBadge.label}
                            </span>

                            {job.category && (
                                <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-50 text-slate-600 border border-slate-200">
                                    {job.category}
                                </span>
                            )}
                        </div>

                        <div className="flex items-center gap-1 text-[11px] text-slate-500 font-medium">
                            <span className="px-1.5 py-0.5 bg-slate-50 text-slate-600 rounded border border-slate-200 text-[10px]">
                                {job.source}
                            </span>
                            {job.seniority_level && (
                                <span className="text-slate-400 text-[10px]">
                                    • {job.seniority_level}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Job Title & Top Right Mark Applied Action */}
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                        <h3 className="text-sm sm:text-base font-semibold text-slate-900 leading-snug">
                            <button
                                type="button"
                                onClick={() => setModalOpen(true)}
                                className="text-left font-semibold text-slate-900 hover:text-blue-600 transition cursor-pointer inline-flex items-center gap-1.5 group"
                                title="Click to open tailored application & pitch"
                            >
                                <span>{displayTitle}</span>
                                <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 opacity-0 group-hover:opacity-100 transition shrink-0">
                                    Tailor ✨
                                </span>
                            </button>
                        </h3>

                        {/* Company & Location line */}
                        <div className="flex items-center gap-1.5 text-xs text-slate-600 mt-1 flex-wrap">
                            <span className="font-medium text-slate-800">{displayCompany}</span>
                            <span className="text-slate-300">•</span>
                            <span className="text-slate-500" title={job.original_location || displayLocation}>
                                {displayLocation}
                            </span>
                            {job.original_location && job.original_location !== displayLocation && (
                                <span className="text-[10px] text-slate-400 font-mono">
                                    (source: {job.original_location})
                                </span>
                            )}
                        </div>
                        </div>

                        {/* Top Right: Mark Applied / Applied Button */}
                        <div className="shrink-0 pt-0.5">
                            {currentStatus === "applied" ? (
                                <button
                                    type="button"
                                    onClick={handleUnmarkApplied}
                                    disabled={isSaving}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition shadow-xs whitespace-nowrap cursor-pointer active:scale-95"
                                    title="Status: Applied! Click to unmark"
                                >
                                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                        <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <span>Applied</span>
                                </button>
                            ) : currentStatus === "pending_approval" ? (
                                <button
                                    type="button"
                                    onClick={() => setModalOpen(true)}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg transition shadow-2xs whitespace-nowrap cursor-pointer active:scale-95"
                                    title="Tailored pitch drafted. Click to review and approve email outreach"
                                >
                                    <span>⏳ Review & Approve</span>
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    onClick={(e) => handleMarkApplied(e, false)}
                                    disabled={isSaving}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded-lg transition shadow-2xs whitespace-nowrap cursor-pointer active:scale-95"
                                    title="Click to mark this job as Applied in tracker"
                                >
                                    <svg className="w-3 h-3 text-emerald-600" viewBox="0 0 16 16" fill="none">
                                        <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <span>Mark Applied</span>
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Matched Skills Chips */}
                    {job.match_breakdown?.matched_skills && job.match_breakdown.matched_skills.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap pt-0.5">
                            <span className="text-[10px] uppercase font-semibold text-slate-400 mr-0.5">
                                Skills:
                            </span>
                            {job.match_breakdown.matched_skills.slice(0, 5).map((skill) => (
                                <span
                                    key={skill}
                                    className="text-[10px] font-medium px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded border border-slate-200/60"
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Snippet */}
                    {job.description_snippet && (
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                            {job.description_snippet}
                        </p>
                    )}
                </div>

                {/* Card Footer: Compensation & Actions */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <span
                            className={`text-xs font-medium px-2 py-0.5 rounded-md ${
                                hasSalary
                                    ? "bg-slate-50 text-slate-700 border border-slate-200 font-medium"
                                    : "text-slate-400 text-[11px]"
                            }`}
                        >
                            {hasSalary ? job.salary : "Salary undisclosed"}
                        </span>

                        {currentStatus !== "untracked" && (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wide border ${
                                currentStatus === "applied"
                                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                    : currentStatus === "pending_approval"
                                    ? "bg-amber-50 text-amber-800 border-amber-300"
                                    : "bg-blue-50 text-blue-700 border border-blue-200"
                            }`}>
                                {currentStatus === "applied" 
                                    ? "✓ Applied" 
                                    : currentStatus === "pending_approval" 
                                    ? "⏳ Pending Approval" 
                                    : currentStatus.replace("_", " ")}
                            </span>
                        )}

                        {feedbackMsg && (
                            <span className="text-[11px] font-bold text-emerald-600 animate-in fade-in duration-150">
                                {feedbackMsg}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-1.5 flex-wrap">
                        {currentStatus === "applied" ? (
                            <>
                                <button
                                    type="button"
                                    onClick={() => setModalOpen(true)}
                                    className="px-2.5 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition shadow-2xs cursor-pointer focus:outline-none"
                                    title="View submitted pitch and application materials"
                                >
                                    View Pitch
                                </button>
                                <a
                                    href={job.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-500 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition shadow-2xs whitespace-nowrap cursor-pointer"
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
                        ) : currentStatus === "pending_approval" ? (
                            <>
                                <button
                                    type="button"
                                    onClick={() => setModalOpen(true)}
                                    className="px-3 py-1 text-xs font-bold text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg transition shadow-2xs cursor-pointer"
                                    title="Review drafted outreach email and approve dispatch"
                                >
                                    Review & Send Email →
                                </button>
                                <a
                                    href={job.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-400 hover:text-slate-700 transition"
                                    title="View original job posting"
                                >
                                    <span>Link ↗</span>
                                </a>
                            </>
                        ) : (
                            <>
                                <button
                                    type="button"
                                    onClick={() => setModalOpen(true)}
                                    className="px-2.5 py-1 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition shadow-2xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                    title="Generate tailored cover letter, CV bullets, and recruiter outreach"
                                >
                                    Tailor Application
                                </button>

                                <a
                                    href={job.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={() => {
                                        handleMarkApplied(undefined, true);
                                    }}
                                    className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition shadow-2xs whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-slate-900/20 cursor-pointer"
                                    title="Open external job portal in a new tab (automatically marks as Applied)"
                                >
                                    <span>Apply</span>
                                    <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none">
                                        <path
                                            d="M3 8H13M13 8L9 4M13 8L9 12"
                                            stroke="currentColor"
                                            strokeWidth="1.5"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                </a>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {modalOpen && (
                <ApplicationModal
                    job={job}
                    initialTab={currentStatus === "pending_approval" || currentStatus === "applied" ? "email" : "cv"}
                    onClose={() => setModalOpen(false)}
                    onStatusChange={(newStatus: string) => {
                        setCurrentStatus(newStatus as "saved" | "pending_approval" | "applied" | "interview" | "rejected" | "follow_up" | "untracked");
                        if (onStatusChange) onStatusChange(newStatus);
                    }}
                />
            )}
        </>
    );
}