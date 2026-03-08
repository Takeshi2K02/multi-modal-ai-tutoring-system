import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

const TOC = ({ data, onBack }) => {
    // data is the full result object from decomposeGoal
    const { toc, goal } = data;
    const [activeSubtopic, setActiveSubtopic] = useState(null);

    return (
        <div className="h-screen w-screen bg-edu-bg-light dark:bg-edu-bg-dark overflow-y-auto p-8 font-sans transition-colors">
            {/* Header */}
            <div className="max-w-4xl mx-auto mb-8">
                <button
                    onClick={onBack}
                    className="mb-4 text-xs font-bold text-zinc-500 dark:text-slate-400 uppercase tracking-widest hover:text-primary transition-colors"
                >
                    &larr; Back to Decomposition
                </button>
                <div className="flex items-center gap-3">
                    <span className="text-4xl filter drop-shadow-md">📚</span>
                    <div>
                        <h1 className="text-2xl font-bold text-edu-text-light dark:text-white transition-colors">Table of Contents</h1>
                        <p className="text-zinc-500 dark:text-slate-400 transition-colors">Learning Path: {goal}</p>
                    </div>
                </div>
            </div>

            <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left: Syllabus Tree */}
                <div className="lg:col-span-2 space-y-8">
                    {toc.map((section, sIdx) => (
                        <div key={sIdx} className="bg-white dark:bg-zinc-900/10 rounded-xl shadow-sm dark:shadow-none border border-edu-border-light dark:border-white/5 overflow-hidden transition-all">
                            <div className="bg-zinc-100/50 dark:bg-zinc-800/30 px-6 py-4 border-b border-edu-border-light dark:border-white/5 flex justify-between items-center transition-colors">
                                <div>
                                    <span className="block text-[10px] font-bold text-primary uppercase tracking-widest mb-1 transition-colors">{section.type.replace("_", " ")}</span>
                                    <h2 className="font-bold text-edu-text-light dark:text-white transition-colors">{section.title}</h2>
                                </div>
                            </div>
                            <div className="divide-y divide-edu-border-light dark:divide-white/5 transition-colors">
                                <div className="p-2 space-y-1">
                                    {section.children.map((child, cIdx) => {
                                        const isActive = activeSubtopic === child;
                                        return (
                                            <div
                                                key={cIdx}
                                                onClick={() => setActiveSubtopic(child)}
                                                className={clsx(
                                                    "cursor-pointer p-3 rounded-lg transition-all border text-sm flex justify-between items-center group",
                                                    isActive
                                                        ? "bg-primary/10 border-primary/30 text-primary shadow-sm"
                                                        : "bg-white dark:bg-transparent border-transparent hover:bg-zinc-50 dark:hover:bg-white/5 hover:border-edu-border-light dark:hover:border-white/5 text-zinc-600 dark:text-slate-300"
                                                )}
                                            >
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{child.title}</span>
                                                    <span className="text-[10px] text-zinc-400 dark:text-slate-500 group-hover:text-primary transition-colors">
                                                        Src: {child.evidence.sourceDocs[0]}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-zinc-300 dark:text-slate-700 group-hover:text-primary transition-all group-hover:translate-x-1">➜</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Right: Content Preview */}
                <div className="lg:col-span-1">
                    <div className="sticky top-8 bg-white dark:bg-zinc-900/10 rounded-xl shadow-lg dark:shadow-none border border-edu-border-light dark:border-white/5 overflow-hidden h-[calc(100vh-100px)] flex flex-col transition-all">
                        <div className="p-4 bg-primary text-white transition-colors">
                            <h3 className="font-bold text-sm uppercase tracking-widest">
                                {activeSubtopic ? "Content Preview" : "Select a Topic"}
                            </h3>
                        </div>

                        <div className="p-6 flex-1 overflow-y-auto">
                            {activeSubtopic ? (
                                <div className="space-y-6">
                                    <div>
                                        <h2 className="text-xl font-bold text-edu-text-light dark:text-white mb-2 transition-colors">
                                            {activeSubtopic.title}
                                        </h2>
                                        <div className="flex gap-2 mb-4">
                                            {activeSubtopic.evidence.sourceDocs.map((src, i) => (
                                                <span key={i} className="px-2 py-1 bg-zinc-100 dark:bg-white/5 text-zinc-400 dark:text-slate-500 text-[10px] rounded border border-edu-border-light dark:border-white/5 transition-colors">
                                                    Ref: {src}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h4 className="text-xs font-bold text-zinc-400 dark:text-slate-500 uppercase tracking-widest transition-colors">
                                            Evidence from VectorDB
                                        </h4>
                                        {activeSubtopic.evidence.topChunks.map((chunk, i) => (
                                            <div key={i} className="bg-zinc-50 dark:bg-white/[0.02] p-4 rounded-lg border border-edu-border-light dark:border-white/5 text-sm text-zinc-600 dark:text-slate-300 leading-relaxed font-serif transition-colors">
                                                "{chunk.text}"
                                            </div>
                                        ))}
                                    </div>

                                    <div className="pt-6 border-t border-edu-border-light dark:border-white/5 transition-colors">
                                        <button className="w-full py-3 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-all active:scale-[0.98] shadow-lg shadow-primary/20">
                                            Start Lesson →
                                        </button>
                                        <p className="text-center text-xs text-zinc-400 dark:text-slate-600 mt-2 transition-colors">
                                            Simulates navigating to lesson player.
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-zinc-300 dark:text-slate-700 text-center p-6 transition-colors">
                                    <span className="text-4xl mb-4 opacity-50 filter grayscale">👈</span>
                                    <p className="text-sm">Click on any subtopic on the left to confirm VectorDB coverage and preview content.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default TOC;
