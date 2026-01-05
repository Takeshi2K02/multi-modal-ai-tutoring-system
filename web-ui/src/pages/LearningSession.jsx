import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { getSession } from '../services/api';

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

    if (loading) return <div className="h-screen flex items-center justify-center text-slate-400">Loading Session...</div>;
    if (!sessionData) return <div className="h-screen flex items-center justify-center text-red-400">Session Not Found</div>;

    const { session, plan } = sessionData;

    return (
        <div className="flex h-screen w-screen bg-slate-50 overflow-hidden font-sans">
            {/* Sidebar: Curriculum Navigator */}
            <div className="w-80 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col h-full z-10">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 backdrop-blur">
                    <button onClick={onBack} className="text-xs text-slate-400 hover:text-slate-600 mb-2 uppercase tracking-wider font-bold">
                        &larr; Back
                    </button>
                    <h2 className="text-sm font-bold text-slate-800 leading-tight line-clamp-2">
                        {plan.original_goal}
                    </h2>
                    <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-emerald-500 rounded-full"
                                style={{ width: `${session.progress.percent_complete}%` }}
                            />
                        </div>
                        <span className="text-[10px] font-mono text-slate-400">{session.progress.percent_complete}%</span>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-4">
                    {plan.curriculum.structure.map((lecture, lIdx) => (
                        <div key={lIdx} className="space-y-1">
                            <div className="px-2 py-1 bg-slate-50/50 rounded flex items-center justify-between group">
                                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider group-hover:text-slate-600 transition-colors">
                                    {lecture.title}
                                </span>
                            </div>
                            <div className="space-y-0.5 ml-1 border-l-2 border-slate-100 pl-2">
                                {lecture.children.map((topic, tIdx) => {
                                    const isActive = activeTopic && activeTopic.title === topic.title;
                                    const isCompleted = session.progress.completed_topics.includes(topic.title);

                                    return (
                                        <button
                                            key={tIdx}
                                            onClick={() => setActiveTopic(topic)}
                                            className={clsx(
                                                "w-full text-left px-3 py-2 rounded-md text-sm transition-all flex items-center justify-between group",
                                                isActive ? "bg-indigo-50 text-indigo-700 font-semibold shadow-sm ring-1 ring-indigo-200" : "text-slate-600 hover:bg-slate-50",
                                                isCompleted && !isActive && "text-emerald-700 bg-emerald-50/50"
                                            )}
                                        >
                                            <span className="truncate">{topic.title}</span>
                                            {isCompleted && <span className="text-emerald-500 text-xs">✓</span>}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Area: Learning Content */}
            <div className="flex-1 flex flex-col h-full bg-slate-50 relative overflow-hidden">
                {/* Top Bar */}
                <div className="h-16 px-8 flex items-center justify-between bg-white/80 backdrop-blur border-b border-slate-200 z-10">
                    <div>
                        <h1 className="text-xl font-bold text-slate-800">
                            {activeTopic ? activeTopic.title : "Select a Topic"}
                        </h1>
                        {activeTopic && (
                            <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                                <span>Evidence Source: {activeTopic.evidence_source_summary?.[0] || 'Unknown'}</span>
                            </div>
                        )}
                    </div>

                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-50 shadow-sm">
                            Ask Agent
                        </button>
                        <button className="px-4 py-2 bg-emerald-500 text-white text-sm font-bold rounded-lg shadow-emerald-200 shadow-md hover:bg-emerald-600 transform hover:scale-105 transition-all">
                            Mark as Complete
                        </button>
                    </div>
                </div>

                {/* Content Scroll Area */}
                <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTopic ? activeTopic.title : 'empty'}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 min-h-[60vh] flex flex-col items-center justify-center text-center"
                        >
                            {activeTopic ? (
                                <>
                                    <div className="mb-6 p-4 bg-indigo-50 rounded-full w-20 h-20 flex items-center justify-center text-indigo-500 text-4xl">
                                        📖
                                    </div>
                                    <h2 className="text-2xl font-bold text-slate-800 mb-4">Ready to Learn: {activeTopic.title}</h2>
                                    <p className="text-slate-500 max-w-lg mx-auto leading-relaxed mb-8">
                                        This topic is grounded in <strong>{activeTopic.evidence_source_summary?.length || 1}</strong> retrieved documents.
                                        Use the "Ask Agent" button to start an interactive tutoring session focused specifically on this concept.
                                    </p>
                                    <div className="grid grid-cols-2 gap-4 w-full max-w-lg">
                                        <div className="p-4 rounded-xl border border-slate-100 bg-slate-50 text-left">
                                            <span className="text-xs font-bold text-slate-400 uppercase">Concept</span>
                                            <p className="font-semibold text-slate-700">{activeTopic.title}</p>
                                        </div>
                                        <div className="p-4 rounded-xl border border-slate-100 bg-slate-50 text-left">
                                            <span className="text-xs font-bold text-slate-400 uppercase">Context</span>
                                            <p className="font-semibold text-slate-700">{plan.original_goal}</p>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <p className="text-slate-400">Select a topic from the sidebar to begin.</p>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default LearningSession;
