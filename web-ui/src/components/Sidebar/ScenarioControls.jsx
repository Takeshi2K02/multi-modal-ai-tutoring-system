import React from 'react';
import { motion } from 'framer-motion';

// Note: Ensure framer-motion is installed: npm install framer-motion
// If not available, we fall back to standard CSS transitions.

const ScenarioCard = ({ title, desc, icon, active, onClick, colorClass }) => (
    <button
        onClick={onClick}
        className={`w-full group relative overflow-hidden rounded-xl p-4 text-left transition-all duration-300 border ${active
                ? `bg-white shadow-lg scale-[1.02] border-transparent ring-2 ${colorClass}`
                : 'bg-white/50 border-slate-200 hover:bg-white hover:shadow-md'
            }`}
    >
        <div className="flex items-start gap-4 relative z-10">
            <div className={`p-3 rounded-lg text-2xl ${active ? 'bg-slate-100' : 'bg-white'}`}>
                {icon}
            </div>
            <div>
                <h3 className={`font-bold text-sm ${active ? 'text-slate-800' : 'text-slate-600'}`}>
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
        <aside className="w-96 flex flex-col h-full bg-slate-50/80 backdrop-blur-md border-r border-slate-200 z-20 shadow-xl">
            {/* Header */}
            <div className="p-6 border-b border-slate-200/60 bg-white/50">
                <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                    <span className="text-2xl">⚡️</span>
                    <span>Antigravity<span className="text-blue-600">Core</span></span>
                </h1>
                <p className="text-xs text-slate-500 mt-1 font-medium tracking-wide uppercase">
                    Agentic Tree of Thought Debugger
                </p>
            </div>

            {/* Controls */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">

                {/* Scenario Selection */}
                <section>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 block">
                        Select Student Persona
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
                                ? 'bg-slate-400 cursor-wait'
                                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-blue-500/25'
                            }`}
                    >
                        <div className="flex items-center justify-center gap-2 relative z-10">
                            {isRunning ? (
                                <>
                                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                                    <span>Reasoning in progress...</span>
                                </>
                            ) : (
                                <span>Run Simulation</span>
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
                            <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">Completed</span>
                        </div>

                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-4">
                            <div>
                                <div className="text-xs text-slate-400 mb-1">Final Response</div>
                                <p className="text-sm text-slate-700 leading-relaxed font-medium">
                                    {outcome.meta?.final_response || "No response generated."}
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-100">
                                <div className="text-center p-2 bg-slate-50 rounded-lg">
                                    <div className="text-xs text-slate-500">Tree Depth</div>
                                    <div className="text-lg font-bold text-slate-800">{outcome.meta?.run_stats?.depth}</div>
                                </div>
                                <div className="text-center p-2 bg-slate-50 rounded-lg">
                                    <div className="text-xs text-slate-500">Nodes Explored</div>
                                    <div className="text-lg font-bold text-slate-800">{outcome.meta?.run_stats?.total_nodes}</div>
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
