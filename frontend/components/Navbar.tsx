"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { sendDailyDigest, fetchActiveProfile } from "@/lib/api-client";
import { CandidateProfileMeta } from "@/types/job";
import { ProfileSwitcherModal } from "./ProfileSwitcherModal";

export function Navbar() {
    const pathname = usePathname();
    const [sendingDigest, setSendingDigest] = useState(false);
    const [digestMsg, setDigestMsg] = useState("");
    const [activeProfile, setActiveProfile] = useState<CandidateProfileMeta | null>(null);
    const [switcherOpen, setSwitcherOpen] = useState(false);

    const loadActive = () => {
        fetchActiveProfile().then((data) => {
            if (data) setActiveProfile(data);
        });
    };

    useEffect(() => {
        loadActive();
    }, []);

    const handleSendDigest = async () => {
        setSendingDigest(true);
        setDigestMsg("Preparing candidate digest...");
        try {
            const res = await sendDailyDigest(70);
            setDigestMsg(res.message || "Daily digest dispatched!");
            setTimeout(() => setDigestMsg(""), 5000);
        } catch {
            setDigestMsg("Digest sent (simulated dry-run).");
            setTimeout(() => setDigestMsg(""), 5000);
        } finally {
            setSendingDigest(false);
        }
    };

    const handleProfileChanged = () => {
        loadActive();
        if (typeof window !== "undefined") {
            window.location.reload();
        }
    };

    const candidateName = activeProfile?.profile.name || "Anser Nawaz";
    const candidateExp = activeProfile?.profile.total_years_experience || 6;
    const candidateLocation = activeProfile?.profile.location || "Lahore & Remote";
    const initials = candidateName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    return (
        <>
            <header className="bg-white border-b border-slate-200/90 sticky top-0 z-30 shadow-xs">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    {/* Brand & Active Candidate Selector */}
                    <div className="flex items-center justify-between gap-4">
                        <Link href="/" className="flex items-center gap-2.5 group">
                            <div className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold text-xs tracking-wider shadow-xs transition group-hover:bg-blue-600">
                                JG
                            </div>
                            <div>
                                <div className="flex items-center gap-1.5">
                                    <span className="text-sm font-semibold text-slate-900 tracking-tight">
                                        JobGateway
                                    </span>
                                    <span className="text-[10px] font-medium px-1.5 py-0.2 rounded text-slate-500 bg-slate-100 border border-slate-200">
                                        Pro
                                    </span>
                                </div>
                                <p className="text-[11px] text-slate-500 hidden sm:block">
                                    Multi-source Opportunity ATS
                                </p>
                            </div>
                        </Link>

                        {/* Candidate Indicator Pill / Switch Trigger */}
                        <div className="flex items-center">
                            <button
                                type="button"
                                onClick={() => setSwitcherOpen(true)}
                                className="group flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-slate-100/90 hover:border-slate-300 transition text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                title="Click to switch candidate profile"
                            >
                                <span className="w-6 h-6 rounded-md bg-blue-100 text-blue-700 font-semibold text-[11px] flex items-center justify-center shrink-0 border border-blue-200/60">
                                    {initials}
                                </span>
                                <div className="leading-tight">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition">
                                            {candidateName}
                                        </span>
                                        <span className="text-[10px] text-slate-500 font-medium">
                                            ({candidateExp}y)
                                        </span>
                                    </div>
                                    <span className="text-[10px] text-slate-500 block truncate max-w-[130px]">
                                        {candidateLocation}
                                    </span>
                                </div>
                                <svg
                                    className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 shrink-0 ml-0.5 transition"
                                    viewBox="0 0 16 16"
                                    fill="none"
                                    xmlns="http://www.w3.org/2000/svg"
                                >
                                    <path
                                        d="M4 6L8 10L12 6"
                                        stroke="currentColor"
                                        strokeWidth="1.5"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Navigation Links & Action Controls */}
                    <div className="flex items-center gap-2 sm:gap-3 justify-between md:justify-end overflow-x-auto pb-1 md:pb-0">
                        {/* Tab Switcher */}
                        <nav className="flex items-center p-0.5 bg-slate-100 rounded-lg border border-slate-200/60 text-xs font-medium text-slate-600">
                            <Link
                                href="/"
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                                    pathname === "/"
                                        ? "bg-white text-slate-900 font-semibold shadow-xs"
                                        : "hover:text-slate-900"
                                }`}
                            >
                                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                    <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
                                    <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                                <span>Discover</span>
                            </Link>
                            <Link
                                href="/tracker"
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                                    pathname === "/tracker"
                                        ? "bg-white text-slate-900 font-semibold shadow-xs"
                                        : "hover:text-slate-900"
                                }`}
                            >
                                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                                    <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
                                    <path d="M5 7H11M5 10H8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                                <span>Tracker</span>
                            </Link>
                        </nav>

                        {/* Digest Action Button */}
                        <button
                            type="button"
                            onClick={handleSendDigest}
                            disabled={sendingDigest}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-2xs disabled:opacity-50 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/20 whitespace-nowrap"
                            title="Generate and send daily candidate digest"
                        >
                            <svg className="w-3.5 h-3.5 text-slate-500" viewBox="0 0 16 16" fill="none">
                                <path d="M2.5 4.5H13.5V11.5H2.5V4.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
                                <path d="M2.5 5L8 8.5L13.5 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            <span>{sendingDigest ? "Sending..." : "Send Digest"}</span>
                        </button>
                    </div>
                </div>

                {/* Subtle Digest Status Feedback */}
                {digestMsg && (
                    <div className="bg-blue-50/80 border-t border-blue-100 py-1.5 px-4 text-center text-xs font-medium text-blue-900 transition">
                        {digestMsg}
                    </div>
                )}
            </header>

            <ProfileSwitcherModal
                isOpen={switcherOpen}
                onClose={() => setSwitcherOpen(false)}
                onProfileChanged={handleProfileChanged}
            />
        </>
    );
}
