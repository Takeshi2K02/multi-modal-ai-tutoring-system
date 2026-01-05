import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Play, Loader2, User, ChevronRight } from 'lucide-react';

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

const ScenarioControls = ({ onRun, isRunning, outcome }) => {
    const [scenario, setScenario] = React.useState('confused');

    return (
        <aside className="w-96 flex flex-col h-full bg-slate-900/90 backdrop-blur-md border-r border-slate-700/50 z-20 shadow-2xl">
            {/* Header */}
            <div className="p-6 border-b border-slate-700/50 bg-slate-900/50">
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <span className="text-blue-500"><Zap size={24} fill="currentColor" /></span>
                    <span>Antigravity<span className="text-slate-500">Core</span></span>
                </h1>
                <p className="text-xs text-slate-500 mt-1 font-medium tracking-wide uppercase flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    Agentic Tree of Thought Debugger
                </p>
            </div>

            {/* Controls */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">

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

                {/* Action Area */}
                <section>
                    <button
                        onClick={() => onRun(scenario)}
                        disabled={isRunning}
                        className={`w-full relative overflow-hidden rounded-xl py-4 font-bold text-sm text-white shadow-lg transition-all transform active:scale-95 ${isRunning
                            ? 'bg-slate-700 cursor-wait'
                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-blue-500/25 hover:brightness-110'
                            }`}
                    >
                        <div className="flex items-center justify-center gap-2 relative z-10">
                            {isRunning ? (
                                <>
                                    <Loader2 className="animate-spin" size={18} />
                                    <span>Reasoning in progress...</span>
                                </>
                            ) : (
                                <>
                                    <Play size={18} fill="currentColor" />
                                    <span>Run Simulation</span>
                                </>
                            )}
                        </div>
                    </button>
                </section>

                {/* Results */}
                {outcome && (
                    <div className="animate-fade-in-up">
                        <div className="flex items-center justify-between mb-3">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                                Agent Decision
                            </label>
                            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full font-bold border border-emerald-500/20">Completed</span>
                        </div>

                        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700/50 p-4 space-y-4">
                            <div>
                                <div className="text-xs text-slate-500 mb-1 font-mono">Final Response</div>
                                <p className="text-sm text-slate-300 leading-relaxed font-medium">
                                    {outcome.meta?.final_response || "No response generated."}
                                </p>
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
                        </div>
                    </div>
                )}
            </div>
        </aside>
    );
};

export default ScenarioControls;
