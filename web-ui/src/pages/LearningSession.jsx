import React, { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import useSWR from 'swr';
import { getSession, fetcher, API_BASE_URL } from '../services/api';
import { ArrowLeft, ArrowRight, BookOpen, CheckCircle, MessageSquare, Book, FileText, ChevronRight, Sparkles, Layers } from 'lucide-react';
import SkeletonTopic from '../components/Skeletons/SkeletonTopic';

const LearningSession = ({ sessionId, onBack, onStartLearning }) => {
    const { data: sessionData, error, isLoading } = useSWR(
        sessionId ? `${API_BASE_URL}/api/session/${sessionId}` : null,
        fetcher
    );
    const [activeTopic, setActiveTopic] = useState(null);

    // Auto-select first topic if none active and data stays loaded
    useEffect(() => {
        if (sessionData?.plan?.curriculum?.structure && !activeTopic) {
            const firstLecture = sessionData.plan.curriculum.structure[0];
            if (firstLecture?.children?.length > 0) {
                setActiveTopic(firstLecture.children[0]);
            }
        }
    }, [sessionData, activeTopic]);

    // STRICT LOADING PROTOCOL: Return ONLY skeleton during fetch
    if (isLoading) return <SkeletonTopic />;

    if (error) return (
        <div className="h-full flex flex-col items-center justify-center text-danger gap-4 bg-edu-bg-light dark:bg-edu-bg-dark transition-colors">
            <div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center border border-danger/20 transition-colors">
                <ArrowLeft size={24} />
            </div>
            <span className="text-sm font-light">Failed to synchronize session.</span>
            <button onClick={onBack} className="text-xs text-primary hover:text-primary/80 uppercase tracking-widest font-bold transition-colors">Return to Dashboard</button>
        </div>
    );

    const { session, plan } = sessionData || {};

    // DATA INTEGRITY GUARD: Prevent render if core structures are missing
    if (!session || !plan || !plan.curriculum?.structure) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-zinc-500 dark:text-slate-500 gap-4 bg-edu-bg-light dark:bg-black transition-colors">
                <span className="text-sm font-light">Initializing cognitive state...</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col lg:flex-row h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark overflow-hidden font-sans selection:bg-primary/30 transition-colors">
            {/* Sidebar: Curriculum Navigator (Grounded Sidebar) */}
            <div className="w-full lg:w-80 flex-shrink-0 bg-white/40 dark:bg-zinc-900/10 border-b lg:border-b-0 lg:border-r border-edu-border-light dark:border-white/5 flex flex-col h-auto lg:h-full z-10 overflow-hidden backdrop-blur-3xl transition-colors">
                <div className="p-6 border-b border-edu-border-light dark:border-white/5 bg-white/60 dark:bg-white/[0.02] shrink-0 transition-colors">
                    <button onClick={onBack} className="text-[10px] text-zinc-400 dark:text-slate-500 hover:text-primary dark:hover:text-white mb-6 uppercase tracking-[0.2em] font-bold flex items-center gap-2 group transition-colors">
                        <ArrowLeft size={12} className="group-hover:-translate-x-1 transition-transform" />
                        Dashboard
                    </button>
                    <h2 className="text-xl font-light text-edu-text-light dark:text-white leading-tight line-clamp-2 mb-6 tracking-tight">
                        {plan.original_goal || "Synthesizing Goal..."}
                    </h2>
                    <div className="space-y-2">
                        <div className="flex justify-between items-end mb-1">
                            <span className="text-[9px] font-bold text-zinc-400 dark:text-slate-500 uppercase tracking-widest transition-colors">Mastery</span>
                            <span className="text-xs font-mono text-secondary font-bold transition-colors">{session?.progress?.percent_complete || 0}%</span>
                        </div>
                        <div className="h-1 bg-zinc-100 dark:bg-white/5 rounded-full overflow-hidden transition-colors">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${session?.progress?.percent_complete || 0}%` }}
                                className="h-full bg-gradient-to-r from-secondary to-teal-400 shadow-[0_0_8px_rgba(16,185,129,0.3)]"
                            />
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                    {plan?.curriculum?.structure?.map((lecture, lIdx) => (
                        <div key={lIdx} className="space-y-2">
                            <div className="px-2 py-1 flex items-center justify-between group">
                                <span className="text-[10px] font-bold uppercase text-zinc-400 dark:text-slate-500 tracking-[0.15em] group-hover:text-primary transition-colors">
                                    {lecture.title}
                                </span>
                            </div>
                            <div className="space-y-1 ml-1 border-l border-edu-border-light dark:border-white/5 pl-3 transition-colors">
                                {lecture?.children?.map((topic, tIdx) => {
                                    const isActive = activeTopic && activeTopic.title === topic.title;
                                    const isCompleted = session?.progress?.completed_topics?.includes(topic.title);

                                    return (
                                        <button
                                            key={tIdx}
                                            onClick={() => setActiveTopic(topic)}
                                            className={clsx(
                                                "w-full text-left px-3 py-3 rounded-xl text-sm flex items-center justify-between group relative overflow-hidden transition-colors",
                                                isActive ? "bg-primary/10 dark:bg-white/5 text-primary dark:text-white font-medium shadow-sm border border-primary/20 dark:border-white/5" : "text-zinc-500 dark:text-slate-500 hover:bg-zinc-50 dark:hover:bg-white/[0.05] hover:text-primary dark:hover:text-slate-300",
                                                isCompleted && !isActive && "text-secondary/60"
                                            )}
                                        >
                                            {isActive && <motion.div layoutId="activeTopic" className="absolute left-0 top-2 bottom-2 w-0.5 bg-primary rounded-full" />}
                                            <span className="truncate pr-2 font-light tracking-tight">{topic.title}</span>
                                            {isCompleted && <CheckCircle size={14} className="text-secondary shrink-0 opacity-80" />}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Area: Learning Content (Zen-mode) */}
            <div className="flex-1 flex flex-col h-full bg-edu-bg-light dark:bg-edu-bg-dark relative overflow-hidden transition-colors">
                {/* Subtle Mesh Background */}
                <div className="absolute inset-0 pointer-events-none opacity-30 dark:opacity-30">
                    <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full" />
                </div>

                {/* Top Bar */}
                <div className="h-20 px-6 lg:px-12 flex items-center justify-between bg-white/60 dark:bg-zinc-900/10 backdrop-blur-3xl border-b border-edu-border-light dark:border-white/5 z-20 gap-8 transition-colors">
                    <div className="min-w-0">
                        <div className="flex items-center gap-2 text-[10px] text-primary uppercase tracking-[0.2em] font-bold mb-1.5">
                            <Sparkles size={12} className="animate-pulse" />
                            Active Trajectory
                        </div>
                        <h1 className="text-xl lg:text-2xl font-light text-edu-text-light dark:text-white truncate max-w-2xl tracking-tight">
                            {activeTopic ? activeTopic.title : "Select a Topic"}
                        </h1>
                    </div>

                    <div className="flex gap-4 shrink-0">
                        <button
                            onClick={() => onStartLearning && onStartLearning(activeTopic)}
                            disabled={!activeTopic}
                            className="px-6 py-3 bg-primary text-white text-sm font-bold rounded-full shadow-2xl shadow-primary/10 hover:bg-primary/90 hover:scale-[1.02] active:scale-95 flex items-center gap-2 disabled:opacity-50 disabled:pointer-events-none transition-all"
                        >
                            <BookOpen size={16} strokeWidth={2.5} />
                            <span>Resume Synthesis</span>
                        </button>
                        <button className="hidden lg:flex px-6 py-3 bg-white dark:bg-white/5 border border-edu-border-light dark:border-white/5 text-zinc-500 dark:text-slate-400 text-sm font-medium rounded-full hover:bg-zinc-50 dark:hover:bg-white/10 hover:text-primary dark:hover:text-white items-center gap-2 transition-colors">
                            <CheckCircle size={16} />
                            <span>Verify Completion</span>
                        </button>
                    </div>
                </div>

                {/* Content Scroll Area */}
                <div className="flex-1 overflow-y-auto p-6 lg:p-12 z-10 custom-scrollbar">
                    <div className="max-w-4xl mx-auto w-full relative">
                        {/* Static Frame */}
                        <div className="bg-white/80 dark:bg-white/[0.02] backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 lg:p-16 min-h-[60vh] flex flex-col items-center justify-center text-center relative overflow-hidden shadow-sm dark:shadow-2xl transition-all">
                            <div className="w-full h-full flex flex-col items-center justify-center">
                                {activeTopic ? (
                                    <div className="relative z-10 max-w-2xl w-full">
                                        <div className="mb-10 p-8 bg-zinc-50 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/5 rounded-[32px] w-28 h-28 flex items-center justify-center text-primary mx-auto shadow-sm dark:shadow-2xl overflow-hidden relative group transition-all">
                                            <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            <Book size={44} strokeWidth={1.5} className="relative z-10" />
                                        </div>

                                        <h2 className="text-3xl lg:text-4xl font-light text-edu-text-light dark:text-white mb-8 leading-tight tracking-tight transition-colors">
                                            {activeTopic.title}
                                        </h2>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                                            <div className="bg-primary/5 dark:bg-primary/10 rounded-3xl p-6 border border-primary/10 dark:border-primary/20 backdrop-blur-md transition-colors">
                                                <h4 className="flex items-center gap-2 text-[10px] font-bold text-zinc-400 dark:text-slate-500 uppercase tracking-widest mb-4 transition-colors">
                                                    <FileText size={14} className="text-primary" /> Grounded Evidence
                                                </h4>
                                                <p className="text-zinc-600 dark:text-slate-400 leading-relaxed text-[13px] font-light transition-colors">
                                                    Synthesized from <strong>{activeTopic.evidence_source_summary?.length || 1}</strong> sources.
                                                    High factual density path prepared.
                                                </p>
                                            </div>

                                            <div className="bg-secondary/5 dark:bg-secondary/10 rounded-3xl p-6 border border-secondary/10 dark:border-secondary/20 backdrop-blur-md flex flex-col justify-center transition-colors">
                                                <div className="space-y-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">1</div>
                                                        <span className="text-xs text-zinc-600 dark:text-slate-300 font-light transition-colors">Review Core Chunks</span>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center text-[10px] font-bold text-secondary">2</div>
                                                        <span className="text-xs text-zinc-600 dark:text-slate-300 font-light transition-colors">Execute Interactive Simulation</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => onStartLearning && onStartLearning(activeTopic)}
                                            className="mt-12 group inline-flex items-center gap-3 px-10 py-5 bg-primary text-white font-bold rounded-full hover:bg-primary/90 shadow-xl shadow-primary/20 transition-all"
                                        >
                                            <span>Initialize Synthesis</span>
                                            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-zinc-300 dark:text-slate-700 flex flex-col items-center transition-colors">
                                        <div className="w-20 h-20 bg-zinc-50 dark:bg-white/[0.02] rounded-full flex items-center justify-center mb-6 border border-edu-border-light dark:border-white/5 transition-all">
                                            <Layers size={32} strokeWidth={1} className="opacity-20 grayscale" />
                                        </div>
                                        <p className="font-light tracking-wide text-sm transition-colors">Select a knowledge module to begin</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LearningSession;
