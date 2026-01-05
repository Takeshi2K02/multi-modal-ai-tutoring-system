import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { User, Medal, ArrowUp, Zap, HelpCircle } from 'lucide-react';

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
        <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-700/50 overflow-hidden flex flex-col h-full ring-1 ring-white/10">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <User size={64} />
                </div>
                <h3 className="text-[10px] font-bold uppercase tracking-widest opacity-80 mb-1 flex items-center gap-1">
                    <Zap size={10} /> Active Student Model
                </h3>
                <div className="flex justify-between items-end relative z-10">
                    <h2 className="text-xl font-bold tracking-tight">{profile.name}</h2>
                    <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-sm font-bold border border-white/10 flex items-center gap-1">
                        <Medal size={10} />
                        Level: {profile.mastery_level}
                    </span>
                </div>
            </div>

            <div className="p-4 flex-1 overflow-y-auto bg-slate-900/50">
                {/* Tie Break Alert */}
                {tieTrace && tieTrace.triggered && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 bg-amber-500/10 border border-amber-500/30 rounded-lg p-3"
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">⚖️</span>
                            <h4 className="text-sm font-bold text-amber-400 uppercase">Tie-Break Event</h4>
                        </div>
                        <p className="text-xs text-amber-300/80 mb-2 leading-relaxed">
                            Path scores were too close. Resolved by <strong>{tieTrace.resolution}</strong>.
                        </p>
                        <div className="space-y-1">
                            {tieTrace.candidates.map((cand, idx) => (
                                <div key={idx} className="flex justify-between text-xs text-amber-200/60 bg-amber-500/5 px-2 py-1 rounded border border-amber-500/10">
                                    <span className="truncate max-w-[120px]">{cand.content}</span>
                                    <span className="font-mono">{cand.score.toFixed(2)} (Pref: {cand.pref_conf.toFixed(2)})</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Top Strategies */}
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <ArrowUp size={10} /> Top Learning Strategies
                </h4>
                <div className="space-y-4">
                    {sortedPrefs.map((pref, idx) => (
                        <div key={idx} className="group relative">
                            <div className="flex justify-between items-center mb-1.5">
                                <span className="text-sm font-medium text-slate-300 flex items-center gap-2 group-hover:text-white transition-colors">
                                    <span className="opacity-80 group-hover:opacity-100 grayscale group-hover:grayscale-0 transition-all">{pref.meta.icon}</span>
                                    {pref.meta.label}
                                </span>
                                <span className={clsx(
                                    "text-xs font-mono font-bold",
                                    pref.confidence > 0.7 ? "text-emerald-400" : "text-slate-500"
                                )}>
                                    {(pref.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                            {/* Bar */}
                            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${pref.confidence * 100}%` }}
                                    className={clsx(
                                        "h-full rounded-full transition-all duration-1000",
                                        pref.confidence > 0.8 ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" :
                                            pref.confidence > 0.6 ? "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" : "bg-slate-600"
                                    )}
                                />
                            </div>
                            <div className="flex justify-between mt-1 opacity-0 group-hover:opacity-100 transition-opacity translate-y-1 group-hover:translate-y-0 duration-300">
                                <span className="text-[9px] text-slate-500 font-mono">Trials: {pref.trials}</span>
                                <span className="text-[9px] text-slate-500 font-mono">Wins: {pref.successes}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-slate-800/50 p-3 border-t border-slate-700/50 text-center text-[10px] text-slate-500 font-mono">
                LAST OPTIMIZED: {profile.last_updated ? new Date(profile.last_updated).toLocaleTimeString() : "Just now"}
            </div>
        </div>
    );
};

export default StudentProfilePanel;
