import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { decomposeGoal } from '../services/api';

const Card = ({ title, children, className }) => (
    <div className={clsx("bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden", className)}>
        <div className="bg-slate-50 px-4 py-3 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-bold text-slate-700 text-sm uppercase tracking-wide">{title}</h3>
        </div>
        <div className="p-4">
            {children}
        </div>
    </div>
);

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
        <div className="h-screen w-screen bg-slate-50 overflow-y-auto p-8 font-sans">
            {/* Header */}
            <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Curriculum Structuring Agent</h1>
                    <p className="text-slate-500 text-sm">Infers structure from VectorDB Metadata or Semantic Clusters</p>
                </div>
                <button
                    onClick={onBack}
                    className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                    &larr; Back to Visualizer
                </button>
            </div>

            {/* Input Section */}
            <div className="max-w-5xl mx-auto bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-8">
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Learning Goal</label>
                <div className="flex gap-4">
                    <input
                        type="text"
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900"
                        placeholder="e.g. I want to learn linear algebra"
                        onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                    />
                    <button
                        onClick={handleCheck}
                        disabled={loading}
                        className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {loading ? 'Analyzing...' : 'Analyze Structure'}
                    </button>
                </div>
                {error && <p className="mt-2 text-red-500 text-sm">{error}</p>}
            </div>

            {/* Results */}
            <div className="max-w-5xl mx-auto space-y-6 pb-20">
                {result && result.status === "NO_COVERAGE" && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 bg-amber-50 border border-amber-200 rounded-xl text-center">
                        <span className="text-4xl mb-2 block">⚠️</span>
                        <h3 className="text-lg font-bold text-amber-800">No Evidence Found</h3>
                        <p className="text-amber-700">VectorDB contains no content relevant to "{result.goal}".</p>
                    </motion.div>
                )}

                {result && result.status !== "NO_COVERAGE" && (
                    <AnimatePresence mode="wait">
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">

                            {/* Metrics & Actions */}
                            <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-center">
                                <div className="flex gap-8">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-indigo-600">{(result.evidenceCoverage * 100).toFixed(0)}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase tracking-wide">Evidence Coverage</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-emerald-600">{(result.outlineConfidence * 100).toFixed(0)}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase tracking-wide">Outline Confidence</div>
                                    </div>
                                </div>

                                {result.showStartButton && (
                                    <button
                                        onClick={async () => {
                                            setSaving(true);
                                            try {
                                                const { saveLearningPlan } = await import('../services/api');
                                                const saved = await saveLearningPlan(result);
                                                console.log("Plan saved:", saved);
                                                onStart(result); // Proceed to navigation
                                            } catch (e) {
                                                alert("Failed to save learning plan!");
                                                console.error(e);
                                                setSaving(false);
                                            }
                                        }}
                                        disabled={saving}
                                        className="px-6 py-3 bg-emerald-500 text-white font-bold rounded-lg shadow-lg shadow-emerald-200 hover:bg-emerald-600 hover:scale-105 transition-all text-sm flex items-center gap-2 disabled:opacity-70 disabled:cursor-wait"
                                    >
                                        {saving ? 'Saving...' : '🚀 Start Learning (Evidence Backed)'}
                                    </button>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                {/* Column 1: Inferred Curriculum (TOC) */}
                                <div className="md:col-span-2 space-y-6">
                                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-indigo-500" /> Inferred Curriculum ({result.toc.length} Sections)
                                    </h2>
                                    {result.toc.map((node, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm transition-all hover:shadow-md"
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="flex items-center gap-2">
                                                    {node.type === "LECTURE_GROUP" && <span className="bg-indigo-100 text-indigo-700 text-[10px] px-2 py-0.5 rounded font-bold uppercase">Lecture</span>}
                                                    {node.type === "TOPIC_CLUSTER" && <span className="bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded font-bold uppercase">Cluster</span>}
                                                    <h3 className="font-bold text-lg text-slate-800">{node.title}</h3>
                                                </div>
                                                <span className="text-[10px] font-mono text-slate-400">{node.children?.length || 0} Topics</span>
                                            </div>

                                            <div className="mt-4 pt-4 border-t border-slate-100">
                                                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Evidence-Backed Topics</h4>
                                                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                                                    {node.children.map((child, i) => (
                                                        <li key={i} className="flex items-center justify-between">
                                                            <span>{child.title}</span>
                                                            <span className="text-[10px] text-slate-400 italic bg-slate-50 px-1 rounded">
                                                                {child.evidence.sourceDocs[0]}
                                                            </span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>

                                {/* Column 2: Gaps & Analysis */}
                                <div className="space-y-6">
                                    <div>
                                        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4">
                                            <span className="w-2 h-2 rounded-full bg-red-400" /> Gap Analysis
                                        </h2>
                                        <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-4 shadow-sm">
                                            {result.gaps.length === 0 ? (
                                                <p className="text-sm text-emerald-600 text-center py-4">All expected topics found in DB!</p>
                                            ) : (
                                                result.gaps.map((gap, i) => (
                                                    <div key={i} className="flex items-start gap-2 text-sm text-slate-700 border-b border-slate-100 last:border-0 pb-3 last:pb-0">
                                                        <span className="mt-0.5 text-red-400">✕</span>
                                                        <div>
                                                            <span className="font-bold block">{gap.title}</span>
                                                            <span className={clsx("text-[10px] font-bold px-1.5 py-0.5 rounded uppercase mr-2",
                                                                gap.gapType === "PROBABLY_MISSING" ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"
                                                            )}>
                                                                {gap.gapType.replace("_", " ")}
                                                            </span>
                                                            <p className="text-xs text-slate-500 mt-1">{gap.reason}</p>
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>

                                    <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-xs text-indigo-800">
                                        <h4 className="font-bold uppercase mb-2">Agent Reasoning</h4>
                                        <p className="mb-2">Structure inferred from {result.toc[0]?.type === "LECTURE_GROUP" ? "Lecture Metadata" : "Semantic Clustering"}.</p>
                                        <p>Coverage calculated based on retrieved evidence chunks.</p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </AnimatePresence>
                )}
            </div>
        </div>
    );
};

export default GoalDecomposition;
