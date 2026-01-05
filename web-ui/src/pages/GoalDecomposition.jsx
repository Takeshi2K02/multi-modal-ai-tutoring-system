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

                {/* Input Section */}
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
                    {error && (
                        <div className="px-4 pb-3 text-red-400 text-sm flex items-center gap-2">
                            <AlertCircle size={14} />
                            {error}
                        </div>
                    )}
                </div>

                {/* Results Area */}
                <AnimatePresence mode="wait">
                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-8"
                        >
                            {/* Status Cards */}
                            {result.status === "NO_COVERAGE" ? (
                                <div className="p-8 bg-amber-900/20 border border-amber-500/30 rounded-2xl text-center backdrop-blur-sm">
                                    <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <AlertTriangle className="text-amber-500" size={32} />
                                    </div>
                                    <h3 className="text-xl font-bold text-amber-200 mb-2">No Content Found</h3>
                                    <p className="text-amber-400/80">We couldn't find any relevant learning materials in the Knowledge Base for "{result.goal}".</p>
                                </div>
                            ) : (
                                <>
                                    {/* Metrics & Action Bar */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-5 backdrop-blur-sm flex items-center gap-4">
                                            <div className="p-3 bg-indigo-500/20 rounded-lg">
                                                <BookOpen className="text-indigo-400" size={24} />
                                            </div>
                                            <div>
                                                <div className="text-2xl font-bold text-white">{(result.evidenceCoverage * 100).toFixed(0)}%</div>
                                                <div className="text-xs text-slate-400 uppercase tracking-wider font-bold">Content Coverage</div>
                                            </div>
                                        </div>

                                        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-5 backdrop-blur-sm flex items-center gap-4">
                                            <div className="p-3 bg-emerald-500/20 rounded-lg">
                                                <Zap className="text-emerald-400" size={24} />
                                            </div>
                                            <div>
                                                <div className="text-2xl font-bold text-white">{(result.outlineConfidence * 100).toFixed(0)}%</div>
                                                <div className="text-xs text-slate-400 uppercase tracking-wider font-bold">Plan Confidence</div>
                                            </div>
                                        </div>

                                        {result.showStartButton && (
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
                                                className="bg-emerald-600 hover:bg-emerald-500 text-white p-5 rounded-xl font-bold shadow-lg shadow-emerald-900/20 transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-wait"
                                            >
                                                {saving ? 'Initializing...' : 'Start Learning Path'}
                                                {!saving && <ChevronRight size={20} />}
                                            </button>
                                        )}
                                    </div>

                                    {/* Generated Title Display */}
                                    <div className="text-center py-4">
                                        <span className="text-xs bg-slate-800 text-slate-400 px-3 py-1 rounded-full border border-slate-700">
                                            Generated Curriclum: <span className="text-slate-200 font-bold">{result.generatedTitle || goal}</span>
                                        </span>
                                    </div>

                                    {/* Curriculum Structure */}
                                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                        <div className="lg:col-span-2 space-y-4">
                                            <h2 className="text-slate-300 font-bold text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
                                                <Layers size={16} /> Course Structure
                                            </h2>

                                            {result.toc.map((node, idx) => (
                                                <motion.div
                                                    key={idx}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: idx * 0.1 }}
                                                    className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-6 hover:bg-slate-800/60 transition-colors"
                                                >
                                                    <div className="flex items-start justify-between mb-4">
                                                        <div>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">MODULE {idx + 1}</span>
                                                                <h3 className="font-bold text-lg text-slate-100">{node.title}</h3>
                                                            </div>
                                                        </div>
                                                        <span className="text-xs text-slate-500 font-mono">{node.children?.length || 0} Topics</span>
                                                    </div>

                                                    <ul className="space-y-2">
                                                        {node.children.map((child, i) => (
                                                            <li key={i} className="flex items-start gap-3 group">
                                                                <CheckCircle className="text-slate-600 group-hover:text-emerald-500 transition-colors mt-0.5 shrink-0" size={16} />
                                                                <span className="text-slate-400 text-sm group-hover:text-slate-200 transition-colors">{child.title}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </motion.div>
                                            ))}
                                        </div>

                                        {/* Gaps Panel */}
                                        <div>
                                            <h2 className="text-slate-300 font-bold text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
                                                <AlertCircle size={16} /> Knowledge Gaps
                                            </h2>

                                            <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5 space-y-4">
                                                {result.gaps.length === 0 ? (
                                                    <div className="text-center py-8 text-emerald-400">
                                                        <CheckCircle size={32} className="mx-auto mb-2 opacity-50" />
                                                        <p className="text-sm">Complete Coverage</p>
                                                    </div>
                                                ) : (
                                                    result.gaps.map((gap, i) => (
                                                        <div key={i} className="flex gap-3 text-sm p-3 rounded-lg bg-slate-900/30 border border-slate-800">
                                                            <div className="mt-0.5">
                                                                <div className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                                                            </div>
                                                            <div>
                                                                <div className="font-bold text-slate-200">{gap.title}</div>
                                                                <div className="text-xs text-red-400 mt-1">{gap.gapType.replace("_", " ")}</div>
                                                                <p className="text-xs text-slate-500 mt-1">{gap.reason}</p>
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </div>

                                            <div className="mt-6 bg-indigo-900/20 border border-indigo-500/20 p-4 rounded-xl">
                                                <h4 className="text-indigo-300 font-bold text-xs uppercase mb-2 flex items-center gap-2">
                                                    <BrainCircuit size={14} /> AI Analysis
                                                </h4>
                                                <p className="text-xs text-indigo-200/60 leading-relaxed">
                                                    Structure inferred via semantic clustering of {result.toc.reduce((acc, n) => acc + n.children.length, 0)} retrieved knowledge chunks.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default GoalDecomposition;
