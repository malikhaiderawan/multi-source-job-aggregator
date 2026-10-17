"use client";

import { useState, useEffect } from "react";
import { CandidateProfileMeta } from "@/types/job";
import { fetchProfiles, activateProfile, createCandidateProfile } from "@/lib/api-client";

interface ProfileSwitcherModalProps {
    isOpen: boolean;
    onClose: () => void;
    onProfileChanged: () => void;
}

export function ProfileSwitcherModal({
    isOpen,
    onClose,
    onProfileChanged
}: ProfileSwitcherModalProps) {
    const [profiles, setProfiles] = useState<CandidateProfileMeta[]>([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<"switch" | "add">("switch");

    // Add new candidate form state
    const [newName, setNewName] = useState("");
    const [newHeadline, setNewHeadline] = useState("");
    const [newExp, setNewExp] = useState(5);
    const [newLocation, setNewLocation] = useState("Lahore, Pakistan");
    const [newEmail, setNewEmail] = useState("");
    const [newPhone, setNewPhone] = useState("+92 300 0000000");
    const [newSkills, setNewSkills] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (isOpen) {
            let isMounted = true;
            fetchProfiles().then((data) => {
                if (isMounted) {
                    setProfiles(data);
                    setLoading(false);
                }
            });
            return () => {
                isMounted = false;
            };
        }
    }, [isOpen]);

    const handleSelectProfile = async (profileId: string) => {
        await activateProfile(profileId);
        onProfileChanged();
        onClose();
    };

    const handleCreateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim() || !newHeadline.trim() || !newSkills.trim()) {
            alert("Please fill in candidate name, headline, and skills.");
            return;
        }

        setSaving(true);
        const id = newName.toLowerCase().replace(/[^a-z0-9]/g, "_") + "_" + Math.floor(Math.random() * 1000);
        const skillsArray = newSkills.split(",").map((s) => s.trim()).filter(Boolean);

        try {
            await createCandidateProfile({
                id,
                name: newName.trim(),
                headline: newHeadline.trim(),
                email: newEmail.trim() || "",
                phone: newPhone.trim() || "",
                location: newLocation.trim() || "Lahore, Pakistan",
                total_years_experience: Number(newExp) || 3,
                all_skills: skillsArray,
                activate: true,
            });
            onProfileChanged();
            onClose();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            alert(`Validation error: ${msg}`);
        } finally {
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
            <div className="bg-white rounded-xl max-w-2xl w-full shadow-xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
                {/* Header */}
                <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
                    <div>
                        <h2 className="text-base font-bold text-slate-900 leading-snug">
                            Candidate Profile Switcher
                        </h2>
                        <p className="text-xs text-slate-500 mt-0.5">
                            Switch active candidate to re-score matching positions and isolate application materials.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
                    >
                        ✕
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-200 bg-slate-50/50 px-5 gap-4 text-xs font-medium">
                    <button
                        type="button"
                        onClick={() => setTab("switch")}
                        className={`py-2.5 border-b-2 transition cursor-pointer ${
                            tab === "switch"
                                ? "border-blue-600 text-blue-600 font-semibold"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Candidates ({profiles.length})
                    </button>
                    <button
                        type="button"
                        onClick={() => setTab("add")}
                        className={`py-2.5 border-b-2 transition cursor-pointer ${
                            tab === "add"
                                ? "border-blue-600 text-blue-600 font-semibold"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        + Add New Candidate
                    </button>
                </div>

                {/* Content */}
                <div className="p-5 sm:p-6 overflow-y-auto flex-1">
                    {tab === "switch" ? (
                        loading ? (
                            <div className="py-12 text-center text-xs text-slate-400">Loading candidate profiles...</div>
                        ) : (
                            <div className="space-y-3">
                                {profiles.map((p) => {
                                    const prof = p.profile;
                                    return (
                                        <div
                                            key={p.id}
                                            className={`p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                                                p.is_active
                                                    ? "bg-blue-50/40 border-blue-200 ring-1 ring-blue-500/20"
                                                    : "bg-white border-slate-200 hover:border-slate-300"
                                            }`}
                                        >
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <h3 className="text-sm font-semibold text-slate-900">{prof.name}</h3>
                                                    {p.is_active && (
                                                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-600 text-white">
                                                            ACTIVE CANDIDATE
                                                        </span>
                                                    )}
                                                    <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                                                        {prof.total_years_experience} Yrs Exp
                                                    </span>
                                                </div>
                                                <p className="text-xs text-slate-600 font-medium">
                                                    {prof.headline}
                                                </p>
                                                <p className="text-[11px] text-slate-400">
                                                    📍 {prof.location} • 📧 {prof.email}
                                                </p>
                                                <div className="flex items-center gap-1 mt-1 flex-wrap">
                                                    {prof.all_skills.slice(0, 5).map((sk) => (
                                                        <span
                                                            key={sk}
                                                            className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600"
                                                        >
                                                            {sk}
                                                        </span>
                                                    ))}
                                                    {prof.all_skills.length > 5 && (
                                                        <span className="text-[10px] text-slate-400">
                                                            +{prof.all_skills.length - 5}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="shrink-0">
                                                {p.is_active ? (
                                                    <span className="text-xs font-semibold text-blue-700 px-3 py-1.5 rounded-lg bg-blue-100/70 inline-block">
                                                        Active
                                                    </span>
                                                ) : (
                                                    <button
                                                        type="button"
                                                        onClick={() => handleSelectProfile(p.id)}
                                                        className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-white shadow-2xs transition cursor-pointer"
                                                    >
                                                        Select
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )
                    ) : (
                        <form onSubmit={handleCreateProfile} className="space-y-3.5 text-xs">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block font-semibold text-slate-700 mb-1">Full Name:</label>
                                    <input
                                        type="text"
                                        required
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                        placeholder="e.g. Malik Haider"
                                        className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block font-semibold text-slate-700 mb-1">Years of Experience:</label>
                                    <input
                                        type="number"
                                        step="0.5"
                                        required
                                        value={newExp}
                                        onChange={(e) => setNewExp(Number(e.target.value))}
                                        className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block font-semibold text-slate-700 mb-1">Headline / Role Title:</label>
                                <input
                                    type="text"
                                    required
                                    value={newHeadline}
                                    onChange={(e) => setNewHeadline(e.target.value)}
                                    placeholder="e.g. Senior Python Developer | AI Specialist"
                                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                />
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block font-semibold text-slate-700 mb-1">Email:</label>
                                    <input
                                        type="email"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
                                        placeholder="candidate@example.com"
                                        className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block font-semibold text-slate-700 mb-1">Phone:</label>
                                    <input
                                        type="text"
                                        value={newPhone}
                                        onChange={(e) => setNewPhone(e.target.value)}
                                        placeholder="+92 300 1234567"
                                        className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block font-semibold text-slate-700 mb-1">Location:</label>
                                <input
                                    type="text"
                                    value={newLocation}
                                    onChange={(e) => setNewLocation(e.target.value)}
                                    placeholder="e.g. Lahore, Pakistan"
                                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                />
                            </div>

                            <div>
                                <label className="block font-semibold text-slate-700 mb-1">
                                    Technical Skills (Comma-separated):
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newSkills}
                                    onChange={(e) => setNewSkills(e.target.value)}
                                    placeholder="e.g. Python, FastAPI, React, PostgreSQL, Docker, AWS"
                                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none"
                                />
                                <p className="text-[11px] text-slate-400 mt-1">
                                    The matching engine computes job match scores against these verified skills.
                                </p>
                            </div>

                            <div className="pt-2 flex justify-end">
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition disabled:opacity-50 cursor-pointer"
                                >
                                    {saving ? "Saving..." : "Save & Activate"}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
