import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, BookOpen, ChevronRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { decomposeGoal } from '../services/api';

/**
 * GoalDecomposition Component
 * 
 * DESIGN RATIONALE:
 * 1. Cognitive Ease: Centered layout and ample white space (padding) reduce visual scanning effort.
 * 2. Functional Minimalism: Removed heavy gradients and glowing borders to focus on the content.
 * 3. Neutral Palette: Using Zinc/Slate (950 to 400 range) creates a calm, professional environment.
 * 4. Micro-interactions: Subtle scale and opacity transitions provide feedback without distraction.
 */
const GoalDecomposition = ({ onStart }) => {
    const [goal, setGoal] = useState("");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [isFocused, setIsFocused] = useState(false);

    const handleCheck = async () => {
        if (!goal.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const data = await decomposeGoal(goal);
            setResult(data);
        } catch (err) {
            console.error(err);
            setError("Unable to generate curriculum. Please check your connection.");
        } finally {
            setLoading(false);
        }
    };

    const handleStartPath = async () => {
        setSaving(true);
        try {
            const { saveLearningPlan, createSession } = await import('../services/api');
            const saved = await saveLearningPlan(result);
            const session = await createSession(saved.plan_id, "student_001");
            onStart(session.session_id);
        } catch (e) {
            const msg = e.response?.data?.detail || "Failed to initialize learning path.";
            setError(msg);
            setSaving(false);
        }
    };

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark font-sans selection:bg-primary/30 overflow-y-auto transition-colors">
            <div className="max-w-3xl mx-auto px-6 py-12 relative z-10">

                {/* Header Section: Premium Typography */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="mb-16 text-center"
                >
                    <h1 className="text-5xl md:text-6xl font-light tracking-tight text-edu-text-light dark:text-white mb-6">
                        Define your <br />
                        <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-primary via-accent to-primary animate-gradient-x shadow-sm">
                            Learning Goal
                        </span>
                    </h1>
                    <p className="text-zinc-500 dark:text-slate-400 text-lg md:text-xl font-light leading-relaxed max-w-lg mx-auto transition-colors">
                        A generative AI core designed to architect your path from curiosity to mastery.
                    </p>
                </motion.div>

                {/* Command Bar style Input: Seamless capsule with breathing focus */}
                <div className="relative mb-20">
                    <motion.div
                        animate={{
                            boxShadow: isFocused
                                ? "0 0 40px -10px rgba(0, 119, 182, 0.3)"
                                : "0 0 20px -12px rgba(0, 0, 0, 0.1)",
                            borderColor: isFocused ? "#0077B6" : "rgba(144, 224, 239, 0.1)"
                        }}
                        className={clsx(
                            "relative flex items-center bg-white/80 dark:bg-[#1E293B]/15 backdrop-blur-2xl rounded-full border border-edu-border-light dark:border-[#90E0EF]/10 p-1 pr-1.5 group transition-all duration-500",
                            isFocused ? "bg-white dark:bg-[#1E293B]/30" : ""
                        )}
                    >
                        {/* Search Icon */}
                        <div className="pl-6 pr-2 text-zinc-400 dark:text-zinc-500">
                            <Search size={20} strokeWidth={1.5} className={clsx(isFocused && "text-primary transition-colors duration-300")} />
                        </div>

                        {/* Input Field */}
                        <input
                            type="text"
                            value={goal}
                            onFocus={() => setIsFocused(true)}
                            onBlur={() => setIsFocused(false)}
                            onChange={(e) => setGoal(e.target.value)}
                            className="flex-1 bg-transparent py-5 px-2 text-edu-text-light dark:text-zinc-200 placeholder-zinc-300 dark:placeholder-zinc-700 focus:outline-none text-xl font-light tracking-tight transition-colors"
                            placeholder="Quantum Computing for Beginners..."
                            onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                        />

                        {/* Action Button: Integrated into capsule */}
                        <button
                            onClick={handleCheck}
                            disabled={loading}
                            className="relative pl-8 pr-4 py-4 bg-primary text-white hover:opacity-90 font-semibold rounded-full transition-all duration-300 active:scale-95 disabled:opacity-50 flex items-center gap-2 overflow-hidden shadow-lg shadow-primary/20"
                        >
                            <AnimatePresence mode="wait">
                                {loading ? (
                                    <motion.div
                                        key="loader"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin"
                                    />
                                ) : (
                                    <motion.div
                                        key="static"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="flex items-center gap-2"
                                    >
                                        <Sparkles size={18} className="text-white animate-pulse" />
                                        <span className="text-[15px] tracking-tight">Generate</span>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </button>
                    </motion.div>

                    {/* Progress Indicator (Subtle) */}
                    {loading && (
                        <motion.div
                            layoutId="progress-bar"
                            className="absolute -bottom-4 left-8 right-8 h-[1px] bg-white/5 overflow-hidden rounded-full"
                        >
                            <motion.div
                                initial={{ x: "-100%" }}
                                animate={{ x: "100%" }}
                                transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                className="w-1/3 h-full bg-gradient-to-r from-transparent via-primary to-transparent"
                            />
                        </motion.div>
                    )}

                    {error && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="absolute -bottom-12 left-0 right-0 text-center text-zinc-500 text-[13px] font-light flex items-center justify-center gap-2"
                        >
                            <AlertCircle size={14} className="text-danger/60" />
                            {error}
                        </motion.div>
                    )}
                </div>

                {/* Results Area */}
                <AnimatePresence>
                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            transwition={{ type: "spring", damping: 30, stiffness: 150 }}
                            className="space-y-12"
                        >
                            {/* Result Summary Header */}
                            <div className="flex items-center justify-center gap-6">
                                <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-edu-border-light dark:to-zinc-800" />
                                <div className="flex items-center gap-3 px-4 py-2 rounded-full border border-edu-border-light dark:border-zinc-800/50 bg-edu-surface-light dark:bg-zinc-900/20 backdrop-blur-sm transition-colors">
                                    <BookOpen size={16} className="text-primary/80" strokeWidth={1.5} />
                                    <span className="text-xs uppercase tracking-[0.2em] font-medium text-zinc-500 dark:text-zinc-400 leading-none">
                                        {result.toc.length} Modules Mapped
                                    </span>
                                </div>
                                <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-edu-border-light dark:to-zinc-800" />
                            </div>

                            {/* Confidence Indicator: Minimalist pill */}
                            <div className="flex items-center gap-6 px-4">
                                <span className="text-[11px] uppercase tracking-widest text-zinc-400 dark:text-zinc-600 font-bold whitespace-nowrap">Plan Accuracy</span>
                                <div className="flex-1 h-[2px] bg-zinc-200 dark:bg-zinc-900 overflow-hidden rounded-full transition-colors">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${result.outlineConfidence * 100}%` }}
                                        transition={{ duration: 1, ease: "circOut" }}
                                        className="h-full bg-primary shadow-[0_0_12px_rgba(0,119,182,0.4)]"
                                    />
                                </div>
                                <span className="text-[13px] font-mono text-edu-text-light dark:text-white/80 select-none transition-colors">
                                    {(result.outlineConfidence * 100).toFixed(0)}%
                                </span>
                            </div>

                            {/* Modules List: Spaced, breathable rhythm */}
                            <div className="space-y-6">
                                {result.toc.map((module, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.08 }}
                                        className="group p-8 rounded-[32px] border border-edu-border-light dark:border-[#90E0EF]/10 bg-white/50 dark:bg-[#1E293B]/15 hover:bg-white dark:hover:bg-[#1E293B]/30 transition-all duration-500 relative overflow-hidden shadow-sm hover:shadow-xl"
                                    >
                                        <div className="absolute top-0 right-0 p-8 text-7xl font-bold opacity-[0.02] transition-opacity group-hover:opacity-[0.04] pointer-events-none select-none">
                                            {idx + 1}
                                        </div>

                                        <div className="flex items-start gap-10 relative z-10">
                                            <div className="shrink-0 flex flex-col items-center">
                                                <div className="w-10 h-10 rounded-full border border-edu-border-light dark:border-zinc-800 flex items-center justify-center text-xs font-mono text-zinc-400 dark:text-zinc-500 group-hover:border-primary/30 group-hover:text-primary transition-all">
                                                    {String(idx + 1).padStart(2, '0')}
                                                </div>
                                                <div className="w-[1px] h-full bg-gradient-to-b from-edu-border-light dark:from-zinc-800 to-transparent mt-4 opacity-50 group-hover:from-primary/20" />
                                            </div>

                                            <div className="flex-1">
                                                <h4 className="text-2xl font-light text-zinc-100 mb-6 tracking-tight leading-tight uppercase tracking-[0.05em]">{module.title}</h4>
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-12">
                                                    {module.children.map((child, i) => (
                                                        <div key={i} className="flex items-center gap-4 text-zinc-500 dark:text-zinc-500 text-[14px] group/item transition-colors">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-800 group-hover/item:bg-primary transition-colors" />
                                                            <span className="group-hover/item:text-edu-text-light dark:group-hover/item:text-zinc-200 transition-colors">{child.title}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            {/* Primary CTA Section */}
                            {result.showStartButton && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="pt-16 pb-24 text-center"
                                >
                                    <button
                                        onClick={handleStartPath}
                                        disabled={saving}
                                        className="inline-flex items-center gap-3 px-10 py-6 rounded-full bg-primary text-white font-bold text-lg hover:bg-primary/90 hover:scale-105 active:scale-95 transition-all duration-500 shadow-xl shadow-primary/20 group"
                                    >
                                        {saving ? (
                                            <div className="w-6 h-6 border-3 border-zinc-900/30 border-t-zinc-900 rounded-full animate-spin" />
                                        ) : (
                                            <>
                                                <span>Begin Learning Path</span>
                                                <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                            </>
                                        )}
                                    </button>
                                    <div className="mt-8 flex items-center justify-center gap-2 text-[10px] uppercase tracking-[0.4em] text-zinc-400 dark:text-zinc-600 transition-colors">
                                        <div className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800" />
                                        <span>Agentic Core Verified</span>
                                        <div className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800" />
                                    </div>
                                </motion.div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default GoalDecomposition;
