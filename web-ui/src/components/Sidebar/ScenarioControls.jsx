import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Play, Loader2, User, ChevronRight, CheckCircle } from 'lucide-react';

const ScenarioCard = ({ title, desc, icon, active, onClick, colorClass }) => (
    <button
        onClick={onClick}
        className={`w-full group relative overflow-hidden rounded-xl p-4 text-left transition-all duration-300 border ${active
            ? `bg-slate-800 shadow-lg scale-[1.02] border-transparent ring-2 ${colorClass}`
            : 'bg-slate-800/40 border-slate-700 hover:bg-slate-800 hover:shadow-md'
            }`}
    >
        <div className="flex items-start gap-4 relative z-10">
            <div className={`p-3 rounded-lg text-2xl ${active ? 'bg-slate-700' : 'bg-slate-900/50'} transition-colors`}>
                {icon}
            </div>
            <div>
                <h3 className={`font-bold text-sm ${active ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'} transition-colors`}>
                    {title}
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    {desc}
                </p>
            </div>
        </div>
        {/* Active Indicator */}
        {active && <div className="absolute top-0 right-0 p-1.5 bg-blue-500 rounded-bl-xl shadow-sm text-[8px] font-bold text-white uppercase tracking-wider">Active</div>}
    </button>
);

const ScenarioControls = ({ onRun, isRunning, outcome, topicContext }) => {
    const [scenario, setScenario] = React.useState('confused');

    return (
        <div className="w-80 h-full bg-slate-900 border-r border-slate-800 flex flex-col z-20 shadow-2xl">
            {/* Header */}
            <div className="p-5 border-b border-slate-800 bg-slate-900/50 backdrop-blur">
                <div className="flex items-center gap-2 text-indigo-400 mb-1">
                    <Zap size={16} />
                    <h2 className="text-xs font-bold uppercase tracking-widest">Agent Debugger</h2>
                </div>
                <h1 className="text-xl font-bold text-white tracking-tight">Strategy Simulation</h1>
                {topicContext && (
                    <div className="mt-3 p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                        <p className="text-[10px] text-indigo-300 font-bold uppercase mb-1">Current Active Context</p>
                        <p className="text-xs text-white leading-tight font-medium line-clamp-2">{topicContext.title}</p>
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-6">

                {/* Disclaimer */}
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 text-xs text-slate-400 italic">
                    <span className="text-slate-200 font-bold not-italic">Note:</span> This view exposes the internal "Tree of Thought" reasoning process. In a production student-facing app, this would happen invisibly in the background.
                </div>

                {/* Scenario Selection */}
                <section>
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 block flex items-center gap-2">
                        <User size={12} /> Select Student Persona
                    </label>
                    <div className="space-y-3">
                        <ScenarioCard
                            title="Confused Student"
                            desc="Low grasp, needs breakdown. CV detects confusion."
                            icon="😕"
                            active={scenario === 'confused'}
                            onClick={() => setScenario('confused')}
                            colorClass="ring-blue-500"
                        />
                        <ScenarioCard
                            title="Bored Student"
                            desc="High grasp but low engagement. Needs gamification."
                            icon="🥱"
                            active={scenario === 'bored'}
                            onClick={() => setScenario('bored')}
                            colorClass="ring-purple-500"
                        />
                    </div>
                </section>

                {/* Run Button */}
                <button
                    onClick={() => onRun("confused")} // Default to confused logic for demo
                    disabled={isRunning}
                    className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-900/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden"
                >
                    {isRunning ? (
                        <>
                            <Loader2 className="animate-spin" size={20} />
                            <span>Thinking...</span>
                        </>
                    ) : (
                        <>
                            <Play size={20} className="fill-white" />
                            <span>Run Strategy Simulation</span>
                        </>
                    )}
                </button>

                {/* Outcome Panel */}
                <AnimatePresence>
                    {outcome && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 space-y-3 overflow-hidden"
                        >
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                <CheckCircle size={14} className="text-emerald-500" />
                                Optimal Strategy Found
                            </h3>
                            <div className="text-sm text-white font-medium p-3 bg-slate-900/50 rounded-lg border border-slate-800 leading-relaxed shadow-inner">
                                {outcome.meta.final_response}
                            </div>
                            <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-700/50">
                                <div className="text-center p-2 bg-slate-900/50 rounded-lg border border-slate-700/30">
                                    <div className="text-xs text-slate-500 mb-1">Tree Depth</div>
                                    <div className="text-lg font-bold text-white">{outcome.meta?.run_stats?.depth}</div>
                                </div>
                                <div className="text-center p-2 bg-slate-900/50 rounded-lg border border-slate-700/30">
                                    <div className="text-xs text-slate-500 mb-1">Nodes Explored</div>
                                    <div className="text-lg font-bold text-white">{outcome.meta?.run_stats?.total_nodes}</div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default ScenarioControls;
