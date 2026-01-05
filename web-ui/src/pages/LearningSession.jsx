import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { getSession } from '../services/api';
import { ArrowLeft, BookOpen, CheckCircle, MessageSquare, Book, FileText, ChevronRight } from 'lucide-react';

const LearningSession = ({ sessionId, onBack }) => {
    const [sessionData, setSessionData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTopic, setActiveTopic] = useState(null);

    useEffect(() => {
        if (!sessionId) return;

        setLoading(true);
        getSession(sessionId)
            .then(data => {
                setSessionData(data);
                // Auto-select first topic if none active
                const firstLecture = data.plan.curriculum.structure[0];
                if (firstLecture && firstLecture.children.length > 0) {
                    setActiveTopic(firstLecture.children[0]);
                }
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, [sessionId]);

    if (loading) return (
        <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4">
            <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full" />
            <span className="text-sm font-mono">Loading Session Context...</span>
        </div>
    );

    if (!sessionData) return <div className="h-full flex items-center justify-center text-red-400">Session Not Found</div>;

    const { session, plan } = sessionData;

    return (
        <div className="flex h-full w-full bg-slate-950 overflow-hidden font-sans">
            {/* Sidebar: Curriculum Navigator */}
            <div className="w-80 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col h-full z-10">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur">
                    <button onClick={onBack} className="text-xs text-slate-400 hover:text-white mb-4 uppercase tracking-wider font-bold flex items-center gap-2 group transition-colors">
                        <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
                        Back to Dashboard
                    </button>
                    <h2 className="text-sm font-bold text-white leading-tight line-clamp-2 mb-3">
                        {plan.original_goal}
                    </h2>
                    <div className="flex items-center gap-3">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-emerald-500 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                                style={{ width: `${session.progress.percent_complete}%` }}
                            />
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400 font-bold">{session.progress.percent_complete}%</span>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-4">
                    {plan.curriculum.structure.map((lecture, lIdx) => (
                        <div key={lIdx} className="space-y-1">
                            <div className="px-3 py-2 bg-slate-800/50 rounded-lg flex items-center justify-between group mx-1">
                                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider group-hover:text-slate-200 transition-colors">
                                    {lecture.title}
                                </span>
                            </div>
                            <div className="space-y-0.5 ml-2 border-l border-slate-700 pl-2">
                                {lecture.children.map((topic, tIdx) => {
                                    const isActive = activeTopic && activeTopic.title === topic.title;
                                    const isCompleted = session.progress.completed_topics.includes(topic.title);

                                    return (
                                        <button
                                            key={tIdx}
                                            onClick={() => setActiveTopic(topic)}
                                            className={clsx(
                                                "w-full text-left px-3 py-2.5 rounded-md text-sm transition-all flex items-center justify-between group relative overflow-hidden",
                                                isActive ? "bg-indigo-500/20 text-indigo-300 font-medium" : "text-slate-500 hover:bg-slate-800 hover:text-slate-300",
                                                isCompleted && !isActive && "text-emerald-500/80"
                                            )}
                                        >
                                            {isActive && <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-indigo-500" />}
                                            <span className="truncate pr-2">{topic.title}</span>
                                            {isCompleted && <CheckCircle size={14} className="text-emerald-500 shrink-0" />}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Area: Learning Content */}
            <div className="flex-1 flex flex-col h-full bg-slate-950 relative overflow-hidden">
                {/* Top Bar */}
                <div className="h-16 px-8 flex items-center justify-between bg-slate-900/80 backdrop-blur border-b border-slate-800 z-10">
                    <div>
                        <div className="flex items-center gap-2 text-xs text-indigo-400 uppercase tracking-widest font-bold mb-1">
                            <BookOpen size={12} />
                            Current Topic
                        </div>
                        <h1 className="text-lg font-bold text-white truncate max-w-xl">
                            {activeTopic ? activeTopic.title : "Select a Topic"}
                        </h1>
                    </div>

                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 hover:scale-105 transition-all flex items-center gap-2">
                            <MessageSquare size={16} />
                            <span>Ask Tutor</span>
                        </button>
                        <button className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2">
                            <CheckCircle size={16} />
                            <span>Mark Complete</span>
                        </button>
                    </div>
                </div>

                {/* Content Scroll Area */}
                <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTopic ? activeTopic.title : 'empty'}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="bg-slate-900/40 rounded-3xl border border-slate-800 p-12 min-h-[60vh] flex flex-col items-center justify-center text-center relative overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 pointer-events-none" />

                            {activeTopic ? (
                                <div className="relative z-10 max-w-2xl">
                                    <div className="mb-8 p-6 bg-slate-800 rounded-full w-24 h-24 flex items-center justify-center text-indigo-400 mx-auto shadow-xl shadow-black/20 ring-1 ring-white/10">
                                        <Book size={40} />
                                    </div>
                                    <h2 className="text-3xl font-bold text-white mb-6 leading-tight">{activeTopic.title}</h2>

                                    <div className="bg-slate-800/60 rounded-xl p-6 mb-8 border border-white/5 backdrop-blur-sm text-left">
                                        <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                            <FileText size={14} /> Context Source
                                        </h4>
                                        <p className="text-slate-300 leading-relaxed text-sm">
                                            This topic is derived from <strong>{activeTopic.evidence_source_summary?.length || 1}</strong> verified sources in your knowledge base.
                                            The tutor has prepared valid reasoning paths based on these documents.
                                        </p>
                                    </div>

                                    <div className="flex flex-col gap-4">
                                        <div className="p-4 rounded-xl border border-slate-700/50 bg-slate-900/50 text-left flex items-start gap-4">
                                            <div className="mt-1 w-8 h-8 rounded bg-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">1</div>
                                            <div>
                                                <span className="block text-sm font-bold text-slate-200 mb-1">Review Material</span>
                                                <p className="text-xs text-slate-500">Read the source chunks associated with this topic.</p>
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-xl border border-slate-700/50 bg-slate-900/50 text-left flex items-start gap-4">
                                            <div className="mt-1 w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">2</div>
                                            <div>
                                                <span className="block text-sm font-bold text-slate-200 mb-1">Interactive Q&A</span>
                                                <p className="text-xs text-slate-500">Click "Ask Tutor" to verify your understanding.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-slate-500 flex flex-col items-center">
                                    <ChevronRight size={48} className="opacity-20 mb-4" />
                                    <p>Select a module from the left to begin learning.</p>
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default LearningSession;
