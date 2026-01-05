import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Zap, AlertTriangle, CheckCircle, BookOpen, ChevronRight, AlertCircle, Sparkles, Layers, BrainCircuit } from 'lucide-react';
import { decomposeGoal } from '../services/api';

const GoalDecomposition = ({ onBack, onStart }) => {
    const [goal, setGoal] = useState("I want to learn linear algebra");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

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
            setError("Failed to connect to Decomposition Service.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full w-full overflow-y-auto p-4 md:p-8 font-sans scroll-smooth">
            <div className="max-w-4xl mx-auto pb-20">

                {/* Header */}
                <div className="mb-10 text-center">
                    <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-3 tracking-tight">
                        What do you want to master?
                    </h1>
                    <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                        Our AI builds a custom curriculum from verified sources, structured for optimal learning.
                    </p>
                </div>

                {/* Context Input */}
                <div className="bg-slate-900/50 backdrop-blur-md p-1 rounded-2xl shadow-2xl border border-slate-700/50 mb-12 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />

                    <div className="flex flex-col md:flex-row gap-2 relative z-10 p-2">
                        <div className="flex-1 bg-slate-950/50 rounded-xl flex items-center px-4 border border-slate-800 focus-within:border-indigo-500/50 transition-colors">
                            <Search className="text-slate-500 mr-3" size={20} />
                            <input
                                type="text"
                                value={goal}
                                onChange={(e) => setGoal(e.target.value)}
                                className="flex-1 bg-transparent py-4 text-white placeholder-slate-600 focus:outline-none text-lg"
                                placeholder="e.g. Introduction to Quantum Computing"
                                onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                            />
                        </div>
                        <button
                            onClick={handleCheck}
                            disabled={loading}
                            className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-900/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed min-w-[160px]"
                        >
                            {loading ? (
                                <span className="animate-pulse">Building...</span>
                            ) : (
                                <>
                                    <Sparkles size={18} />
                                    <span>Plan Route</span>
                                </>
                            )}
                        </button>
                    </div>

                    {/* Results Section */}
                    {result && (
                        <div className="p-4 md:p-6 animate-fade-in-up">
                            {/* Header Row */}
                            <div className="flex flex-col md:flex-row items-center justify-between mb-6 gap-4">
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <BookOpen size={24} className="text-indigo-400" />
                                    Recommended Curriculum
                                </h3>
                                <span className="text-xs font-mono font-bold text-slate-400 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 uppercase tracking-wider">
                                    {result.toc.length} Modules
                                </span>
                            </div>

                            {/* Main Card */}
                            <div className="bg-slate-950/50 rounded-3xl border border-slate-800/50 overflow-hidden relative">
                                {/* Confidence Visualization (Center) */}
                                <div className="py-12 md:py-16 flex flex-col items-center justify-center relative">
                                    <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 to-transparent opacity-50" />

                                    <div className="relative z-10 w-32 h-32 md:w-40 md:h-40 rounded-full bg-slate-900 border-4 border-slate-800 flex flex-col items-center justify-center shadow-2xl shadow-indigo-900/20 mb-4">
                                        <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent bg-transparent rotate-45" style={{ opacity: result.outlineConfidence }} />
                                        <BrainCircuit className="text-indigo-400 mb-1" size={32} />
                                        <span className="text-3xl md:text-4xl font-extrabold text-white">{(result.outlineConfidence * 100).toFixed(0)}%</span>
                                    </div>
                                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Plan Confidence</p>
                                </div>

                                {/* Start Button (Bottom Full Width) */}
                                {result.showStartButton && (
                                    <div className="p-4 bg-slate-900/50 border-t border-slate-800">
                                        <button
                                            onClick={async () => {
                                                setSaving(true);
                                                try {
                                                    const { saveLearningPlan, createSession } = await import('../services/api');
                                                    const saved = await saveLearningPlan(result);
                                                    const session = await createSession(saved.plan_id, "student_001");
                                                    onStart(session.session_id);
                                                } catch (e) {
                                                    const msg = e.response?.data?.detail || "Failed to start session!";
                                                    alert(`Error: ${msg}`);
                                                    setSaving(false);
                                                }
                                            }}
                                            disabled={saving}
                                            className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-900/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-wait group text-lg"
                                        >
                                            {saving ? 'Initializing Curriculum...' : 'Start Learning Path'}
                                            {!saving && <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    {error && (
                        <div className="px-6 pb-6 text-red-400 text-sm flex items-center gap-2">
                            <AlertCircle size={14} />
                            {error}
                        </div>
                    )}
                </div>

                {/* Modules List (Below Main Card) */}
                <AnimatePresence mode="wait">
                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-4"
                        >
                            <div className="text-center py-4 opacity-50">
                                <ChevronRight className="mx-auto rotate-90" />
                            </div>

                            {result.toc.map((node, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 hover:bg-slate-900/60 transition-colors flex flex-col md:flex-row md:items-start gap-6 group"
                                >
                                    {/* Module Badge (Fixed Width/Height) */}
                                    <div className="shrink-0">
                                        <span className="inline-block px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs font-bold uppercase tracking-wider min-w-[100px] text-center whitespace-nowrap group-hover:bg-indigo-500/20 transition-colors">
                                            Module {idx + 1}
                                        </span>
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1">
                                        <h3 className="text-xl font-bold text-slate-100 mb-3">{node.title}</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {node.children.map((child, i) => (
                                                <div key={i} className="flex items-start gap-2 text-sm text-slate-400">
                                                    <CheckCircle size={14} className="mt-1 text-slate-600 shrink-0 group-hover:text-emerald-500/50 transition-colors" />
                                                    <span>{child.title}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Stats */}
                                    <div className="shrink-0 text-right hidden md:block">
                                        <span className="text-2xl font-bold text-slate-700 block">{String(idx + 1).padStart(2, '0')}</span>
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};


export default GoalDecomposition;
