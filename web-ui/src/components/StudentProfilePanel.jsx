import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

// Map Strategy Keys to Human Readable Labels/Icons if not provided by backend
const STRATEGY_LABELS = {
    "visual_explanation": { label: "Visual Explanation", icon: "🖼️" },
    "scaffolded_steps": { label: "Step-by-Step", icon: "👣" },
    "socratic_questioning": { label: "Socratic Q&A", icon: "🤔" },
    "worked_example": { label: "Worked Example", icon: "📝" },
    "interactive_practice": { label: "Practice Problem", icon: "✍️" },
    "gamified_quiz": { label: "Gamified Quiz", icon: "🎮" },
    "analogy_contextual": { label: "Real-world Analogy", icon: "🌍" },
    "recap_summarize": { label: "Summary", icon: "📑" },
    "motivational_encouragement": { label: "Encouragement", icon: "🌟" },
};

const StudentProfilePanel = ({ profile, tieTrace }) => {
    if (!profile) return null;

    const preferences = profile.learning_preferences || {};

    // Convert to array and sort by confidence
    const sortedPrefs = Object.entries(preferences)
        .map(([key, val]) => ({
            key,
            ...val,
            meta: STRATEGY_LABELS[key] || { label: key, icon: "🔹" }
        }))
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 5); // Top 5

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 text-white">
                <h3 className="text-sm font-bold uppercase tracking-wider opacity-90">Student Model</h3>
                <div className="flex justify-between items-end mt-1">
                    <h2 className="text-xl font-bold">{profile.name}</h2>
                    <span className="text-xs bg-white/20 px-2 py-1 rounded text-white/90">
                        Level: {profile.mastery_level}
                    </span>
                </div>
            </div>

            <div className="p-4 flex-1 overflow-y-auto">
                {/* Tie Break Alert */}
                {tieTrace && tieTrace.triggered && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-3"
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">⚖️</span>
                            <h4 className="text-sm font-bold text-amber-800 uppercase">Tie-Break Event</h4>
                        </div>
                        <p className="text-xs text-amber-700 mb-2">
                            Path scores were too close. Resolved by <strong>{tieTrace.resolution}</strong>.
                        </p>
                        <div className="space-y-1">
                            {tieTrace.candidates.map((cand, idx) => (
                                <div key={idx} className="flex justify-between text-xs text-amber-900/80 bg-white/50 px-2 py-1 rounded">
                                    <span className="truncate max-w-[120px]">{cand.content}</span>
                                    <span className="font-mono">{cand.score.toFixed(2)} (Pref: {cand.pref_conf.toFixed(2)})</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Top Strategies */}
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
                    Top Learning Strategies
                </h4>
                <div className="space-y-3">
                    {sortedPrefs.map((pref, idx) => (
                        <div key={idx} className="group relative">
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                                    <span>{pref.meta.icon}</span> {pref.meta.label}
                                </span>
                                <span className={clsx(
                                    "text-xs font-mono font-bold",
                                    pref.confidence > 0.7 ? "text-emerald-600" : "text-slate-500"
                                )}>
                                    {(pref.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                            {/* Bar */}
                            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${pref.confidence * 100}%` }}
                                    className={clsx(
                                        "h-full rounded-full transition-colors",
                                        pref.confidence > 0.8 ? "bg-emerald-500" :
                                            pref.confidence > 0.6 ? "bg-blue-500" : "bg-slate-300"
                                    )}
                                />
                            </div>
                            <div className="flex justify-between mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-[10px] text-slate-400">Trials: {pref.trials}</span>
                                <span className="text-[10px] text-slate-400">Wins: {pref.successes}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-slate-50 p-3 border-t text-center text-xs text-slate-400">
                Last updated: {profile.last_updated ? new Date(profile.last_updated).toLocaleTimeString() : "Just now"}
            </div>
        </div>
    );
};

export default StudentProfilePanel;
