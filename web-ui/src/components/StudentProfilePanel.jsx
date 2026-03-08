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

const StudentProfilePanel = ({ profile, tieTrace, isDemoMode, demoPersona }) => {
    const activeProfile = profile || {
        name: demoPersona?.name || "Student Model",
        mastery_level: "Analyzing...",
        learning_preferences: {
            "visual_explanation": { confidence: 0.82, trials: 12, successes: 10 },
            "scaffolded_steps": { confidence: 0.65, trials: 8, successes: 5 },
            "worked_example": { confidence: 0.45, trials: 5, successes: 2 }
        }
    };

    const preferences = activeProfile.learning_preferences || {};

    const sortedPrefs = Object.entries(preferences)
        .map(([key, val]) => ({
            key,
            ...val,
            meta: STRATEGY_LABELS[key] || { label: key, icon: "🔹" }
        }))
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 5);

    return (
        <div className="h-full flex flex-col bg-white dark:bg-[#121212] selection:bg-primary/30 transition-colors">
            {/* Header: Glassmorphism */}
            <div className="p-8 bg-white/80 dark:bg-[#1E293B]/15 border-b border-edu-border-light dark:border-[#90E0EF]/10 relative overflow-hidden backdrop-blur-3xl transition-colors">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/10 rounded-full blur-[80px]" />

                <div className="relative z-10">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-edu-border-light dark:border-white/10 shadow-[0_0_20px_rgba(0,119,182,0.1)] transition-colors">
                            <User className="text-primary" size={20} />
                        </div>
                        <div>
                            <span className="text-[10px] uppercase font-black tracking-[0.4em] text-zinc-500 dark:text-slate-500 mb-0.5 block">Student Architecture</span>
                            <div className="h-0.5 w-6 bg-primary/40 rounded-full" />
                        </div>
                    </div>

                    <h2 className="text-3xl font-light text-edu-text-light dark:text-white tracking-tight mb-4 leading-none transition-colors">
                        {activeProfile.name}
                    </h2>
                    <div className="flex items-center gap-3">
                        <span className="px-4 py-1.5 bg-primary/10 border border-primary/30 rounded-full text-[9px] font-black tracking-widest text-primary uppercase shadow-lg shadow-primary/20">
                            Mastery: <span className="text-edu-text-light dark:text-white ml-1">{activeProfile.mastery_level}</span>
                        </span>
                    </div>
                </div>
            </div>

            {/* Content List */}
            <div className="flex-1 p-8 overflow-y-auto custom-scrollbar space-y-12">
                {/* Tie Break Logic */}
                {tieTrace && tieTrace.triggered && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-[#48CAE4]/[0.03] border border-[#48CAE4]/20 rounded-[32px] p-8 backdrop-blur-xl relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <Zap size={40} className="text-accent" />
                        </div>
                        <div className="flex items-center gap-3 mb-6">
                            <Zap size={14} className="text-[#48CAE4] animate-pulse" />
                            <h4 className="text-[10px] font-black text-[#48CAE4] uppercase tracking-[0.3em]">Tie-Break Event</h4>
                        </div>
                        <p className="text-xs text-zinc-500 dark:text-slate-400 mb-6 leading-relaxed font-light">
                            Pedagogical variance detected. Resolution: <span className="text-[#48CAE4] font-bold uppercase tracking-widest ml-1">{tieTrace.resolution}</span>
                        </p>
                        <div className="space-y-3">
                            {tieTrace.candidates.map((cand, idx) => (
                                <div key={idx} className="flex justify-between items-center bg-white dark:bg-[#1E293B]/15 px-5 py-3 rounded-2xl border border-edu-border-light dark:border-[#90E0EF]/10 hover:border-[#48CAE4]/30 transition-all duration-300">
                                    <span className="text-[10px] text-zinc-600 dark:text-slate-300 font-medium truncate max-w-[140px] tracking-tight">{cand.content}</span>
                                    <span className="text-[10px] font-mono text-[#48CAE4] font-black">{cand.score.toFixed(2)}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Cognitive Distribution */}
                <div>
                    <div className="flex items-center justify-between mb-10">
                        <h4 className="text-[10px] font-black text-zinc-500 dark:text-slate-500 uppercase tracking-[0.4em] flex items-center gap-3">
                            <ArrowUp size={12} className="text-secondary" />
                            Preferred Strategies
                        </h4>
                        <div className="h-px flex-1 bg-edu-border-light dark:bg-white/5 ml-4" />
                    </div>

                    <div className="space-y-10">
                        {sortedPrefs.map((pref, idx) => (
                            <div key={idx} className="group cursor-default">
                                <div className="flex justify-between items-end mb-4">
                                    <div className="flex items-center gap-4">
                                        <span className="text-2xl transition-all duration-500 group-hover:scale-125 group-hover:rotate-6 drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]">{pref.meta.icon}</span>
                                        <div>
                                            <span className="text-xs font-bold text-zinc-500 dark:text-slate-400 group-hover:text-edu-text-light dark:group-hover:text-white transition-colors tracking-tight block mb-0.5">{pref.meta.label}</span>
                                            <span className="text-[8px] text-zinc-400 dark:text-slate-600 font-black uppercase tracking-widest">{pref.trials} Trials • {pref.successes} Succ.</span>
                                        </div>
                                    </div>
                                    <span className="text-[10px] font-black text-primary group-hover:text-secondary transition-colors tracking-tighter">
                                        {(pref.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="h-1.5 w-full bg-zinc-100 dark:bg-white/[0.02] rounded-full overflow-hidden border border-edu-border-light dark:border-white/5 transition-colors">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${pref.confidence * 100}%` }}
                                        className="h-full bg-gradient-to-r from-primary via-primary/70 to-secondary group-hover:shadow-[0_0_10px_rgba(0,175,185,0.3)] transition-all duration-700"
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-8 bg-white/50 dark:bg-[#0D0D3B]/90 border-t border-edu-border-light dark:border-[#90E0EF]/10 text-center transition-colors">
                <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white dark:bg-[#1E293B]/15 border border-edu-border-light dark:border-[#90E0EF]/10">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#00AFB9] animate-pulse" />
                    <p className="text-[9px] text-zinc-500 dark:text-slate-600 uppercase font-black tracking-[0.3em]">
                        Last dynamic tuning: <span className="text-zinc-400 dark:text-slate-400 ml-1">{activeProfile.last_updated ? new Date(activeProfile.last_updated).toLocaleTimeString() : "Synchronized"}</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default StudentProfilePanel;
