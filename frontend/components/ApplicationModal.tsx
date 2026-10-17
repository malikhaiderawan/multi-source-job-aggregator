"use client";

import { useState, useEffect } from "react";
import { JobPosting, ApplicationGenerateResponse, ApplicationTrackerItem } from "@/types/job";
import {
    generateApplicationMaterials,
    saveTrackedApplication,
    approveAndSendApplicationEmail,
    fetchActiveProfile,
    buildTrackerId,
    fetchTrackedApplication
} from "@/lib/api-client";

interface ApplicationModalProps {
    job: JobPosting;
    initialTab?: "cv" | "letter" | "email";
    onClose: () => void;
    onStatusChange?: (newStatus: string) => void;
}

export function ApplicationModal({ job, initialTab = "cv", onClose, onStatusChange }: ApplicationModalProps) {
    const [activeTab, setActiveTab] = useState<"cv" | "letter" | "email">(initialTab);
    const [loading, setLoading] = useState(true);
    const [materials, setMaterials] = useState<ApplicationGenerateResponse | null>(null);
    const [candidateId, setCandidateId] = useState<string>("anser_nawaz");
    const [currentStatus, setCurrentStatus] = useState<string>(job.application_status || "untracked");
    const [trackingLoading, setTrackingLoading] = useState(false);
    const [statusNotification, setStatusNotification] = useState<string | null>(null);

    // Email state with STRICT approval gate
    const [recipientEmail, setRecipientEmail] = useState("");
    const [subject, setSubject] = useState("");
    const [emailBody, setEmailBody] = useState("");
    const [approved, setApproved] = useState(false);
    const [sending, setSending] = useState(false);
    const [dispatchResult, setDispatchResult] = useState<string | null>(null);
    const [showSuccessCard, setShowSuccessCard] = useState(false);
    const [copiedMsg, setCopiedMsg] = useState("");

    useEffect(() => {
        let isMounted = true;
        async function load() {
            setLoading(true);
            const activeProf = await fetchActiveProfile();
            const activeId = activeProf?.id || "anser_nawaz";
            if (isMounted) setCandidateId(activeId);

            const trackerId = buildTrackerId(activeId, job);
            const [res, existingItem] = await Promise.all([
                generateApplicationMaterials(job),
                fetchTrackedApplication(trackerId, activeId)
            ]);

            if (isMounted) {
                if (existingItem) {
                    setCurrentStatus(existingItem.status);
                    if (existingItem.email_recipient) {
                        setRecipientEmail(existingItem.email_recipient);
                    }
                    if (existingItem.tailored_recruiter_email) {
                        setEmailBody(existingItem.tailored_recruiter_email);
                    }
                    if (existingItem.email_approved) {
                        setApproved(existingItem.email_approved);
                    }
                    if (existingItem.status === "pending_approval" && initialTab === "cv") {
                        setActiveTab("email");
                    }
                }

                if (res) {
                    setMaterials(res);
                    const name = res.candidate_name || activeProf?.profile?.name || "Candidate";
                    setSubject(`Application: ${job.title} - ${name}`);
                    if (!existingItem?.tailored_recruiter_email) {
                        setEmailBody(res.recruiter_email);
                    }
                    if (!existingItem?.email_recipient) {
                        if (res.suggested_recipient_email) {
                            setRecipientEmail(res.suggested_recipient_email);
                        } else if (job.contact_email) {
                            setRecipientEmail(job.contact_email);
                        }
                    }
                }
                setLoading(false);
            }
        }
        load();
        return () => { isMounted = false; };
    }, [job, initialTab]);

    const handleCopy = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        setCopiedMsg(`${label} copied to clipboard!`);
        setTimeout(() => setCopiedMsg(""), 3000);
    };

    const handleTrack = async (status: ApplicationTrackerItem["status"]) => {
        setTrackingLoading(true);
        setCurrentStatus(status);
        try {
            const trackerId = buildTrackerId(candidateId, job);
            await saveTrackedApplication({
                id: trackerId,
                candidate_id: candidateId,
                job: { ...job, application_status: status },
                status,
                tailored_cv_bullet_points: materials?.tailored_cv_bullet_points || [],
                tailored_cover_letter: materials?.cover_letter || "",
                tailored_recruiter_email: emailBody,
                email_recipient: recipientEmail,
                email_approved: approved
            });
            if (onStatusChange) onStatusChange(status);

            const labels: Record<string, string> = {
                saved: "Bookmarked",
                pending_approval: "Pending Approval",
                applied: "Applied",
                interview: "Interview Stage",
                follow_up: "Follow-up",
                rejected: "Rejected"
            };
            setStatusNotification(`Status saved as "${labels[status] || status}" in Tracker!`);
            setTimeout(() => setStatusNotification(null), 3500);
        } catch (err) {
            console.error("Tracker save failed:", err);
            setStatusNotification("Failed to update tracker. Please try again.");
            setTimeout(() => setStatusNotification(null), 3500);
        } finally {
            setTrackingLoading(false);
        }
    };

    const handleSendApprovedEmail = async () => {
        if (!approved) {
            alert("Security Gate: You must check the approval box before sending.");
            return;
        }
        if (!recipientEmail || !recipientEmail.includes("@")) {
            alert("Please enter a valid recipient email address.");
            return;
        }

        setSending(true);
        setDispatchResult(null);

        try {
            const trackerId = buildTrackerId(candidateId, job);
            const res = await approveAndSendApplicationEmail({
                tracker_id: trackerId,
                recipient_email: recipientEmail,
                subject,
                body_text: emailBody,
                approved: true
            });
            setDispatchResult(res.message);
            setShowSuccessCard(true);
            if (res.status === "sent") {
                setCurrentStatus("applied");
                if (onStatusChange) onStatusChange("applied");
                setStatusNotification("Application successfully transmitted & recorded as Applied!");
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            setDispatchResult(`Error: ${msg}`);
            setShowSuccessCard(true);
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
            <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-xl border border-slate-200 overflow-hidden">
                {/* Header */}
                <div className="p-4 sm:p-5 border-b border-slate-100 flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                {job.match_score}% Match
                            </span>
                            {currentStatus === "applied" && (
                                <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs flex items-center gap-1">
                                    <span>✓</span>
                                    <span>Applied</span>
                                </span>
                            )}
                            <span className="text-xs text-slate-500 font-medium">
                                {job.category} • {job.source}
                            </span>
                        </div>
                        <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                            {job.title}
                        </h2>
                        <p className="text-xs text-slate-500 mt-0.5">
                            {job.company} — 📍 {job.location}
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition whitespace-nowrap cursor-pointer"
                        >
                            <span>Open Job Link</span>
                            <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                <path
                                    d="M4 12L12 4M12 4H6M12 4V10"
                                    stroke="currentColor"
                                    strokeWidth="1.5"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </a>
                        <button
                            type="button"
                            onClick={onClose}
                            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition cursor-pointer"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Sub-Header Tabs */}
                <div className="flex border-b border-slate-200 bg-slate-50/50 px-5 gap-3 text-xs font-medium">
                    <button
                        type="button"
                        onClick={() => setActiveTab("cv")}
                        className={`py-2.5 border-b-2 transition cursor-pointer ${
                            activeTab === "cv"
                                ? "border-blue-600 text-blue-600 font-semibold"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Tailored CV Bullets
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("letter")}
                        className={`py-2.5 border-b-2 transition cursor-pointer ${
                            activeTab === "letter"
                                ? "border-blue-600 text-blue-600 font-semibold"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Cover Letter
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("email")}
                        className={`py-2.5 border-b-2 transition cursor-pointer ${
                            activeTab === "email"
                                ? "border-blue-600 text-blue-600 font-semibold"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Recruiter Email
                    </button>
                </div>

                {/* Content Body */}
                <div className="p-5 sm:p-6 overflow-y-auto flex-1">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-12 space-y-3">
                            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                            <p className="text-xs font-medium text-slate-500">
                                Generating materials tailored to candidate profile...
                            </p>
                        </div>
                    ) : materials ? (
                        <div>
                            {copiedMsg && (
                                <div className="mb-4 p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold text-center">
                                    {copiedMsg}
                                </div>
                            )}

                            {/* Applied Job Guidance Banner */}
                            {currentStatus === "applied" && (
                                <div className="mb-4 p-3 bg-emerald-50 rounded-lg border border-emerald-300 text-emerald-900 text-xs flex items-center justify-between gap-3 shadow-2xs">
                                    <div className="flex items-center gap-2">
                                        <span className="text-base font-bold text-emerald-700">✓</span>
                                        <div>
                                            <strong className="block font-bold text-emerald-950">Application Submitted & Recorded</strong>
                                            <p className="text-[11px] text-emerald-800">
                                                This role is recorded as Applied. Review your tailored pitch, cover letter, and CV below.
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleTrack("interview")}
                                        className="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs transition whitespace-nowrap cursor-pointer active:scale-95"
                                        title="Click if recruiter scheduled an interview"
                                    >
                                        🎉 Got Interview?
                                    </button>
                                </div>
                            )}

                            {/* Tab 1: CV Bullets */}
                            {activeTab === "cv" && (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-sm font-semibold text-slate-900">
                                            Tailored Resume Bullet Points (Factual)
                                        </h3>
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleCopy(
                                                    materials.tailored_cv_bullet_points.join("\n• "),
                                                    "CV Bullets"
                                                )
                                            }
                                            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs"
                                        >
                                            Copy All Bullets
                                        </button>
                                    </div>
                                    <p className="text-xs text-slate-500">
                                        Aligned directly with job requirements from candidate&apos;s verified experience.
                                    </p>
                                    <ul className="space-y-2">
                                        {materials.tailored_cv_bullet_points.map((pt, idx) => (
                                            <li
                                                key={idx}
                                                className="p-3 bg-slate-50/60 rounded-lg border border-slate-200/80 text-xs text-slate-800 leading-relaxed flex items-start gap-2.5"
                                            >
                                                <span className="text-blue-600 font-bold">•</span>
                                                <span className="flex-1">{pt}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Tab 2: Cover Letter */}
                            {activeTab === "letter" && (
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-sm font-semibold text-slate-900">
                                            Personalized Cover Letter
                                        </h3>
                                        <button
                                            type="button"
                                            onClick={() => handleCopy(materials.cover_letter, "Cover Letter")}
                                            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs"
                                        >
                                            Copy Letter
                                        </button>
                                    </div>
                                    <textarea
                                        readOnly
                                        rows={12}
                                        value={materials.cover_letter}
                                        className="w-full p-3.5 border border-slate-200 rounded-lg text-xs text-slate-800 leading-relaxed font-mono bg-slate-50/40 focus:outline-none"
                                    />
                                </div>
                            )}

                            {/* Tab 3: Recruiter Outreach Email */}
                            {activeTab === "email" && (
                                <div className="space-y-3.5">
                                    {currentStatus === "pending_approval" && (
                                        <div className="p-3 bg-amber-50 rounded-lg border border-amber-300 text-amber-900 text-xs flex items-start gap-2 shadow-2xs">
                                            <span className="text-base shrink-0">⏳</span>
                                            <div>
                                                <p className="font-bold">Pending Approval Review Gate</p>
                                                <p className="text-[11px] text-amber-800 mt-0.5 leading-relaxed">
                                                    This application is queued for your review. Check the recipient email, review your pitch, tick the <strong>Explicit Approval Gate</strong> below, and click <strong>Send Approved Email</strong> to dispatch with Anser Nawaz&apos;s verified PDF resume attached.
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {currentStatus === "applied" ? (
                                        <div className="p-3 bg-emerald-50/80 rounded-lg border border-emerald-200/80 space-y-1 text-xs">
                                            <div className="flex items-center justify-between">
                                                <span className="font-semibold text-emerald-950 flex items-center gap-1.5">
                                                    <span>✓ Application Status:</span>
                                                    <span className="text-emerald-700 font-bold">Applied & Recorded</span>
                                                </span>
                                                <a
                                                    href={job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-[11px] font-semibold text-emerald-800 hover:text-emerald-950 underline flex items-center gap-1"
                                                >
                                                    <span>View Original Posting</span>
                                                    <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none">
                                                        <path d="M4 12L12 4M12 4H6M12 4V10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                                                    </svg>
                                                </a>
                                            </div>
                                            <p className="text-[11px] text-emerald-800 leading-relaxed">
                                                Your application for <strong>{job.company}</strong> is submitted. The outreach note and verified CV used for this position are preserved below.
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="p-3 bg-blue-50/80 rounded-lg border border-blue-200/80 space-y-1.5">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs font-semibold text-blue-900 flex items-center gap-1.5">
                                                    <span>ℹ️ Direct Application Portal:</span>
                                                </span>
                                                <a
                                                    href={job.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-[11px] font-semibold text-blue-700 hover:text-blue-900 underline flex items-center gap-1"
                                                >
                                                    <span>Apply on {job.source || "Official Website"}</span>
                                                    <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none">
                                                        <path d="M4 12L12 4M12 4H6M12 4V10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                                                    </svg>
                                                </a>
                                            </div>
                                            <p className="text-[11px] text-blue-800 leading-relaxed">
                                                Companies like <strong>{job.company}</strong> usually receive job applications directly through their careers portal (click the link above to submit your CV). If you locate the recruiter or hiring manager&apos;s email on LinkedIn, you can also paste their email below to send this tailored outreach note directly.
                                            </p>
                                        </div>
                                    )}

                                    <div>
                                        <div className="flex items-center justify-between mb-1">
                                            <label className="block text-xs font-semibold text-slate-700">
                                                Recruiter / Contact Email:
                                            </label>
                                            {recipientEmail && (job.contact_email || materials?.suggested_recipient_email) ? (
                                                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                                    ✨ Auto-detected from posting
                                                </span>
                                            ) : (
                                                <span className="text-[10px] text-slate-400">
                                                    (Paste recruiter email or use direct link above)
                                                </span>
                                            )}
                                        </div>
                                        <input
                                            type="email"
                                            value={recipientEmail}
                                            onChange={(e) => setRecipientEmail(e.target.value)}
                                            placeholder="recruiter@company.com or careers@company.com"
                                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                                            Email Subject:
                                        </label>
                                        <input
                                            type="text"
                                            value={subject}
                                            onChange={(e) => setSubject(e.target.value)}
                                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                                            Email Body (Editable):
                                        </label>
                                        <textarea
                                            rows={8}
                                            value={emailBody}
                                            onChange={(e) => setEmailBody(e.target.value)}
                                            className="w-full p-3 border border-slate-200 rounded-lg text-xs leading-relaxed focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                        />
                                    </div>

                                    {/* Auto-attached PDF Resume Badge */}
                                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                                        <div className="flex items-center gap-2 text-slate-700 font-medium">
                                            <span className="text-base">📎</span>
                                            <div>
                                                <span className="font-semibold text-slate-900">Anser_Nawaz_Resume.pdf</span>
                                                <span className="text-[11px] text-slate-500 block">Auto-attached with cover letter on transmission</span>
                                            </div>
                                        </div>
                                        <a
                                            href="/Anser_Nawaz_Resume.pdf"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-2.5 py-1 text-[11px] font-semibold text-blue-700 bg-white hover:bg-blue-50 border border-blue-200 rounded-md transition shadow-2xs"
                                        >
                                            Preview PDF
                                        </a>
                                    </div>

                                    {/* Strict User Approval Gate or Confirmed Record */}
                                    {currentStatus === "applied" ? (
                                        <div className="space-y-3 pt-1">
                                            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-300 flex items-center justify-between gap-3 shadow-2xs">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-emerald-700 text-lg font-bold">✓</span>
                                                    <div>
                                                        <span className="text-xs font-bold text-emerald-950 block">
                                                            Application Submitted & Outreach Active
                                                        </span>
                                                        <span className="text-[11px] text-emerald-800">
                                                            Recipient: <strong className="font-semibold">{recipientEmail || "Direct Portal / Recruiter"}</strong> • PDF Resume attached
                                                        </span>
                                                    </div>
                                                </div>
                                                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-200/80 text-emerald-900 border border-emerald-300">
                                                    ✓ Applied
                                                </span>
                                            </div>

                                            <div className="flex items-center justify-between pt-1">
                                                <button
                                                    type="button"
                                                    onClick={() => handleCopy(emailBody, "Email Body")}
                                                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs cursor-pointer"
                                                >
                                                    Copy Email Pitch
                                                </button>

                                                <button
                                                    type="button"
                                                    onClick={() => handleTrack("interview")}
                                                    className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition cursor-pointer active:scale-95 flex items-center gap-1.5"
                                                    title="Recruiter responded? Click to advance to Interview stage"
                                                >
                                                    <span>🎉 Got Interview?</span>
                                                </button>
                                            </div>

                                            {/* Re-send expandable gate if user needs to dispatch again */}
                                            <details className="text-[11px] text-slate-400 pt-1">
                                                <summary className="cursor-pointer hover:text-slate-600 font-medium">
                                                    Need to transmit an additional note or re-send?
                                                </summary>
                                                <div className="mt-2 p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                                                    <div className="flex items-start gap-2">
                                                        <input
                                                            type="checkbox"
                                                            id="resend-approval"
                                                            checked={approved}
                                                            onChange={(e) => setApproved(e.target.checked)}
                                                            className="mt-0.5 h-3.5 w-3.5 rounded border-slate-300 text-blue-600 cursor-pointer"
                                                        />
                                                        <label htmlFor="resend-approval" className="text-xs text-slate-700 cursor-pointer">
                                                            Explicit Gate: I approve re-transmitting this email to {recipientEmail || "the recruiter"}.
                                                        </label>
                                                    </div>
                                                    <button
                                                        type="button"
                                                        disabled={!approved || sending}
                                                        onClick={handleSendApprovedEmail}
                                                        className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs disabled:opacity-50 cursor-pointer"
                                                    >
                                                        {sending ? "Transmitting..." : "Re-send Approved Email"}
                                                    </button>
                                                </div>
                                            </details>
                                        </div>
                                    ) : (
                                        <>
                                            {/* Strict User Approval Gate */}
                                            <div className="p-3 bg-amber-50/70 rounded-lg border border-amber-200 flex items-start gap-2.5">
                                                <input
                                                    type="checkbox"
                                                    id="email-approval"
                                                    checked={approved}
                                                    onChange={(e) => setApproved(e.target.checked)}
                                                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                                                />
                                                <label htmlFor="email-approval" className="text-xs text-amber-900 font-medium cursor-pointer">
                                                    Explicit Approval Gate: I have reviewed this application email and explicitly approve transmitting it to {recipientEmail || "the recruiter"}.
                                                </label>
                                            </div>

                                            <div className="flex items-center justify-between pt-2">
                                                <button
                                                    type="button"
                                                    onClick={() => handleCopy(emailBody, "Email Body")}
                                                    className="text-xs text-slate-500 hover:text-slate-800 font-medium underline"
                                                >
                                                    Copy Email Text
                                                </button>
                                                <button
                                                    type="button"
                                                    disabled={!approved || sending}
                                                    onClick={handleSendApprovedEmail}
                                                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                                                >
                                                    {sending ? "Transmitting..." : "Send Approved Email"}
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : (
                        <p className="text-center text-xs text-slate-500 py-8">
                            Unable to load tailored application materials.
                        </p>
                    )}
                </div>

                {/* Instant Status Notification Banner */}
                {statusNotification && (
                    <div className="px-4 py-2 bg-emerald-50 border-t border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between animate-in fade-in duration-150">
                        <span className="flex items-center gap-1.5">
                            <span className="text-sm">✨</span>
                            <span>{statusNotification}</span>
                        </span>
                        <button
                            type="button"
                            onClick={() => setStatusNotification(null)}
                            className="text-emerald-700 hover:text-emerald-950 font-bold ml-2 text-xs cursor-pointer"
                        >
                            ✕
                        </button>
                    </div>
                )}

                {/* Footer Quick Actions */}
                <div className="p-3.5 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-slate-500 font-medium">Save to Tracker:</span>
                        <button
                            type="button"
                            onClick={() => handleTrack("saved")}
                            disabled={trackingLoading}
                            className={`px-2.5 py-1 rounded-md font-semibold transition cursor-pointer active:scale-95 ${
                                currentStatus === "saved"
                                    ? "bg-slate-800 text-white shadow-xs"
                                    : "bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 shadow-2xs"
                            }`}
                        >
                            {currentStatus === "saved" ? "✓ Bookmarked" : "Bookmark"}
                        </button>
                        <button
                            type="button"
                            onClick={() => handleTrack("pending_approval")}
                            disabled={trackingLoading}
                            className={`px-2.5 py-1 rounded-md font-semibold transition cursor-pointer active:scale-95 ${
                                currentStatus === "pending_approval"
                                    ? "bg-amber-600 text-white shadow-xs"
                                    : "bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800"
                            }`}
                        >
                            {currentStatus === "pending_approval" ? "✓ Pending Approval" : "Pending Approval"}
                        </button>
                        <button
                            type="button"
                            onClick={() => handleTrack("applied")}
                            disabled={trackingLoading}
                            className={`px-3 py-1 rounded-md font-bold transition shadow-xs cursor-pointer active:scale-95 ${
                                currentStatus === "applied"
                                    ? "bg-emerald-600 hover:bg-emerald-700 text-white ring-2 ring-emerald-500/30"
                                    : "bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-800"
                            }`}
                        >
                            {currentStatus === "applied" ? "✓ Applied" : "Mark Applied"}
                        </button>
                        {currentStatus === "applied" && (
                            <button
                                type="button"
                                onClick={() => handleTrack("interview")}
                                disabled={trackingLoading}
                                className="px-3 py-1 rounded-md font-bold transition shadow-xs cursor-pointer active:scale-95 bg-purple-50 hover:bg-purple-100 border border-purple-300 text-purple-800"
                                title="Recruiter responded to schedule an interview"
                            >
                                🎉 Got Interview?
                            </button>
                        )}
                        {currentStatus === "interview" && (
                            <span className="px-2.5 py-1 rounded-md font-bold bg-purple-100 text-purple-800 border border-purple-300">
                                🎉 Interview Active
                            </span>
                        )}
                    </div>

                    <button
                        type="button"
                        onClick={onClose}
                        className="px-3.5 py-1.5 bg-slate-200 hover:bg-slate-300 font-semibold rounded-lg text-slate-700 transition cursor-pointer"
                    >
                        Done
                    </button>
                </div>
            </div>

            {/* Prominent Pop-up Success / Result Card */}
            {showSuccessCard && (
                <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
                    <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-7 shadow-2xl border border-emerald-100 flex flex-col items-center text-center">
                        {dispatchResult?.startsWith("Error:") ? (
                            <>
                                <div className="w-14 h-14 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center text-2xl font-bold mb-3 shadow-xs">
                                    ⚠️
                                </div>
                                <h3 className="text-lg font-bold text-slate-900 mb-1">
                                    Transmission Failed
                                </h3>
                                <p className="text-xs text-rose-600 mb-5 leading-relaxed bg-rose-50 border border-rose-200 rounded-xl p-3 w-full text-left">
                                    {dispatchResult}
                                </p>
                                <button
                                    type="button"
                                    onClick={() => setShowSuccessCard(false)}
                                    className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-black text-white font-bold text-xs transition cursor-pointer"
                                >
                                    Dismiss & Fix
                                </button>
                            </>
                        ) : (
                            <>
                                {/* Green Success Badge */}
                                <div className="w-16 h-16 rounded-2xl bg-emerald-500 text-white flex items-center justify-center text-3xl font-extrabold mb-3 shadow-lg shadow-emerald-500/25">
                                    ✓
                                </div>

                                <span className="px-3 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 mb-2">
                                    Dispatched via Live SMTP
                                </span>

                                <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                                    Application Transmitted!
                                </h3>
                                <p className="text-xs text-slate-500 mt-1 mb-5">
                                    Your tailored pitch and verified CV have been sent directly to the employer.
                                </p>

                                {/* Card Details */}
                                <div className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-5 text-left text-xs space-y-2">
                                    <div className="flex items-start justify-between gap-2">
                                        <span className="text-slate-500 font-semibold">Recipient:</span>
                                        <span className="font-bold text-slate-900 truncate max-w-[210px]" title={recipientEmail}>
                                            {recipientEmail}
                                        </span>
                                    </div>
                                    <div className="flex items-start justify-between gap-2">
                                        <span className="text-slate-500 font-semibold">Role:</span>
                                        <span className="font-semibold text-slate-900 truncate max-w-[210px]" title={job.title}>
                                            {job.title}
                                        </span>
                                    </div>
                                    <div className="flex items-start justify-between gap-2">
                                        <span className="text-slate-500 font-semibold">Company:</span>
                                        <span className="font-semibold text-slate-900 truncate max-w-[210px]">
                                            {job.company}
                                        </span>
                                    </div>
                                    <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
                                        <span className="text-slate-500 font-semibold">Attachment:</span>
                                        <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[11px]">
                                            <span>📎</span>
                                            <span>Anser_Nawaz_Resume.pdf</span>
                                        </span>
                                    </div>
                                </div>

                                <p className="text-[11px] text-emerald-700 bg-emerald-50/70 border border-emerald-100 rounded-lg py-1.5 px-3 mb-5 w-full">
                                    ✨ Status updated to <strong>Applied</strong> in Tracker
                                </p>

                                {/* Action Buttons */}
                                <div className="flex items-center gap-2.5 w-full">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowSuccessCard(false);
                                            onClose();
                                        }}
                                        className="flex-1 py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-black text-white font-bold text-xs shadow-sm transition cursor-pointer"
                                    >
                                        Done & Close
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowSuccessCard(false)}
                                        className="py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition cursor-pointer"
                                    >
                                        Keep Open
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
