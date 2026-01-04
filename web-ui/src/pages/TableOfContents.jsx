import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

const TOC = ({ data, onBack }) => {
    // data is the full result object from decomposeGoal
    const { toc, goal } = data;
    const [activeSubtopic, setActiveSubtopic] = useState(null);

    return (
        <div className="h-screen w-screen bg-slate-50 overflow-y-auto p-8 font-sans">
            {/* Header */}
            <div className="max-w-4xl mx-auto mb-8">
                <button
                    onClick={onBack}
                    className="mb-4 text-xs font-bold text-slate-500 uppercase tracking-widest hover:text-slate-800 transition-colors"
                >
                    &larr; Back to Decomposition
                </button>
                <div className="flex items-center gap-3">
                    <span className="text-4xl">📚</span>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">Table of Contents</h1>
                        <p className="text-slate-500">Learning Path: {goal}</p>
                    </div>
                </div>
            </div>

            <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left: Syllabus Tree */}
                <div className="lg:col-span-2 space-y-8">
                    {toc.map((section, sIdx) => (
                        <div key={sIdx} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                            <div className="bg-slate-50 px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                                <div>
                                    <span className="block text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-1">{section.type.replace("_", " ")}</span>
                                    <h2 className="font-bold text-slate-800">{section.title}</h2>
                                </div>
                            </div>
                            <div className="divide-y divide-slate-100">
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
                                                        ? "bg-indigo-50 border-indigo-200 text-indigo-900 shadow-sm"
                                                        : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-200 text-slate-700"
                                                )}
                                            >
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{child.title}</span>
                                                    <span className="text-[10px] text-slate-400 group-hover:text-slate-500">
                                                        Src: {child.evidence.sourceDocs[0]}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-slate-300">➜</span>
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
                    <div className="sticky top-8 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden h-[calc(100vh-100px)] flex flex-col">
                        <div className="p-4 bg-indigo-600 text-white">
                            <h3 className="font-bold text-sm uppercase tracking-widest">
                                {activeSubtopic ? "Content Preview" : "Select a Topic"}
                            </h3>
                        </div>

                        <div className="p-6 flex-1 overflow-y-auto">
                            {activeSubtopic ? (
                                <div className="space-y-6">
                                    <div>
                                        <h2 className="text-xl font-bold text-slate-900 mb-2">
                                            {activeSubtopic.title}
                                        </h2>
                                        <div className="flex gap-2 mb-4">
                                            {activeSubtopic.evidence.sourceDocs.map((src, i) => (
                                                <span key={i} className="px-2 py-1 bg-slate-100 text-slate-500 text-[10px] rounded border border-slate-200">
                                                    Ref: {src}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                                            Evidence from VectorDB
                                        </h4>
                                        {activeSubtopic.evidence.topChunks.map((chunk, i) => (
                                            <div key={i} className="bg-slate-50 p-4 rounded-lg border border-slate-100 text-sm text-slate-700 leading-relaxed font-serif">
                                                "{chunk.text}"
                                            </div>
                                        ))}
                                    </div>

                                    <div className="pt-6 border-t border-slate-100">
                                        <button className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition-colors">
                                            Start Lesson →
                                        </button>
                                        <p className="text-center text-xs text-slate-400 mt-2">
                                            Simulates navigating to lesson player.
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-6">
                                    <span className="text-4xl mb-4 opacity-50">👈</span>
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
