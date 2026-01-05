import React from 'react';
import { motion } from 'framer-motion';

const NodeDetail = ({ node, onClose }) => {
    if (!node) return null;

    const { label, fullContent, localScore, pathScore, depth, type, directive, isBestPath } = node.data;

    return (
        <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            className="fixed top-0 right-0 h-full w-[400px] bg-white shadow-2xl border-l border-slate-200 p-6 overflow-y-auto z-50"
        >
            <div className="flex justify-between items-center mb-6">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Thought Node Detail</span>
                <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                    ×
                </button>
            </div>

            <div className="mb-6">
                <h2 className="text-xl font-bold text-slate-800 mb-2">{type.replace("_", " ")}</h2>
                <div className="flex gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${isBestPath ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                        {isBestPath ? 'Winning Path' : 'Explored Path'}
                    </span>
                    <span className="px-2 py-1 rounded text-xs font-bold uppercase bg-indigo-50 text-indigo-600">
                        Score: {localScore.toFixed(2)}
                    </span>
                </div>
            </div>

            <div className="space-y-6">
                <div>
                    <h3 className="text-sm font-bold text-slate-900 mb-2">Internal Monologue</h3>
                    <div className="p-4 bg-slate-50 rounded-lg text-sm text-slate-700 whitespace-pre-wrap leading-relaxed border border-slate-100 font-mono">
                        {fullContent}
                    </div>
                </div>

                {directive && (
                    <div>
                        <h3 className="text-sm font-bold text-slate-900 mb-2">Next Directive</h3>
                        <div className="p-3 bg-amber-50 rounded-lg text-sm text-amber-900 border border-amber-100">
                            {directive}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default NodeDetail;
