import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Sparkles, ChevronRight, ChevronLeft, Activity, User, ShieldCheck, Zap, PanelLeftClose, PanelRightClose, PanelLeft, PanelRight } from 'lucide-react';
import { io } from 'socket.io-client';
import TreeVisualizer from '../components/Graph/TreeVisualizer';
import StudentProfilePanel from '../components/StudentProfilePanel';

const socket = io('http://localhost:8000');

const ReasoningTerminal = ({ logs, leftExpanded, rightExpanded }) => {
    const terminalRef = React.useRef(null);

    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <motion.div
            animate={{
                left: leftExpanded ? 320 : 20,
                right: rightExpanded ? 320 : 20
            }}
            className="absolute bottom-0 h-40 bg-zinc-900/80 backdrop-blur-xl border-t border-white/5 p-4 font-mono z-30 transition-all duration-500 overflow-hidden flex flex-col"
        >
            <div className="flex items-center gap-2 mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Reasoning Terminal</span>
            </div>
            <div
                ref={terminalRef}
                className="flex-1 overflow-y-auto space-y-1 scrollbar-hide"
            >
                {logs.map((log, i) => (
                    <div key={i} className="text-[10px] text-zinc-400">
                        <span className="text-secondary">[{log.source}]</span> {log.content}
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

const AgentDebugger = ({ context, onComplete }) => {
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [status, setStatus] = useState('Initializing...');
    const [isComplete, setIsComplete] = useState(false);
    const [countdown, setCountdown] = useState(null);
    const [profile] = useState(context?.profile || {});
    const [cvMetrics, setCvMetrics] = useState({ emotion: 'Neutral', score: 0.85, gaze: 'Focused', posture: 'Vertical' });
    const [rlPolicy, setRlPolicy] = useState({});
    const [thoughtStream, setThoughtStream] = useState([]);
    const [finalPayload, setFinalPayload] = useState(null);
    const [showLeftPanel, setShowLeftPanel] = useState(false);
    const [showRightPanel, setShowRightPanel] = useState(false);

    // 1. Real-time Node Discovery & Reasoning Listeners
    useEffect(() => {
        socket.on('node_discovered', (node) => {
            if (context?.synthesis_id && node.synthesis_id !== context.synthesis_id) return;

            setNodes((prev) => {
                const exists = prev.find(n => n.id === node.id);
                if (exists) {
                    // Project ID: 25-26J-130: Update scores for Evaluation visibility
                    return prev.map(n => n.id === node.id ? {
                        ...n,
                        data: {
                            ...n.data,
                            localScore: node.metadata?.localScore || n.data.localScore,
                            pathScore: node.metadata?.pathScore || n.data.pathScore,
                            metadata: { ...n.data.metadata, ...node.metadata }
                        }
                    } : n);
                }

                const newNode = {
                    id: node.id,
                    type: 'thoughtNode',
                    data: {
                        label: node.content,
                        content: node.content,
                        depth: node.depth,
                        localScore: node.metadata?.localScore || 0.0,
                        pathScore: node.metadata?.pathScore || 0.0,
                        metadata: node.metadata
                    },
                    position: { x: 0, y: 0 }
                };
                return [...prev, newNode];
            });

            if (node.parent_id) {
                setEdges((prev) => [
                    ...prev,
                    {
                        id: `e-${node.parent_id}-${node.id}`,
                        source: node.parent_id,
                        target: node.id,
                        animated: true
                    }
                ]);
            }
            setStatus(`Discovering Thought: Depth ${node.depth}`);
        });

        socket.on('thought_stream', (data) => {
            if (context?.synthesis_id && data.synthesis_id !== context.synthesis_id) return;
            setThoughtStream(prev => [...prev.slice(-49), { source: data.source, content: data.content }]);
        });

        socket.on('cv_update', (data) => {
            setCvMetrics({
                emotion: data.emotion,
                score: data.engagement_score,
                gaze: data.gaze,
                posture: data.posture
            });
        });

        socket.on('policy_update', (data) => {
            setRlPolicy(data.distribution);
        });

        socket.on('synthesis_complete', (data) => {
            if (context?.synthesis_id && data.synthesis_id !== context.synthesis_id) return;

            setStatus('Synthesis Complete');
            console.log(">>> [Debugger] Synthesis Complete. Payload Captured:", data);
            setFinalPayload(data);
            setIsComplete(true);
            setCountdown(3); // Project ID: 25-26J-130: 3s Inspection Buffer
        });

        return () => {
            socket.off('node_discovered');
            socket.off('thought_stream');
            socket.off('cv_update');
            socket.off('policy_update');
            socket.off('synthesis_complete');
        };
    }, [context?.synthesis_id]);

    // 2. Automated Handoff Countdown
    useEffect(() => {
        if (countdown === null) return;
        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
            return () => clearTimeout(timer);
        } else {
            // Project ID: 25-26J-130: Ensure handoff only happens if Finalized Path is rendered
            // Fallback: If isComplete is true for >5s, navigate anyway to prevent stall
            const hasFinalNode = nodes.some(n => n.data?.metadata?.type === 'final');
            if (hasFinalNode || isComplete) {
                onComplete && onComplete(finalPayload);
            }
        }
    }, [countdown, onComplete, finalPayload, nodes, isComplete]);

    return (
        <div className="flex h-full w-full bg-zinc-950 text-white relative overflow-hidden font-sans">
            {/* LEFT PANEL: Student Profile */}
            <AnimatePresence>
                {showLeftPanel && (
                    <motion.div
                        initial={{ x: -320 }}
                        animate={{ x: 0 }}
                        exit={{ x: -320 }}
                        className="w-80 h-full bg-zinc-900 border-r border-white/5 p-8 flex flex-col gap-8 z-20 overflow-y-auto shrink-0"
                    >
                        <div>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-6">Student Profile</h3>
                            <div className="space-y-4">
                                <div className="p-5 bg-white/[0.03] rounded-3xl border border-white/10">
                                    <div className="flex items-center gap-3 mb-3">
                                        <User size={14} className="text-primary" />
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Identity</span>
                                    </div>
                                    <p className="text-xl font-light text-white mb-2">{profile.name || "Alex"}</p>
                                    <div className="space-y-3 mt-4">
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Cognitive Modalities</span>
                                        {Object.entries(profile.preferred_modality || {}).map(([key, val]) => (
                                            <div key={key} className="space-y-1">
                                                <div className="flex justify-between text-[10px] uppercase font-bold text-zinc-400">
                                                    <span>{key}</span>
                                                    <span className="text-primary">{val.toFixed(2)}</span>
                                                </div>
                                                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                                    <div className="h-full bg-primary" style={{ width: `${val * 100}%` }} />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-6 pt-4 border-t border-white/5">
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Scaffolding Bias</span>
                                        <p className="text-lg font-mono text-secondary">+{profile.scaffolding_bias || "0.15"}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Panel Toggles */}
            <div className="absolute top-6 left-6 z-[60] flex gap-2">
                <button
                    onClick={() => setShowLeftPanel(!showLeftPanel)}
                    className="p-3 bg-zinc-900/80 backdrop-blur-md border border-white/10 rounded-2xl text-zinc-400 hover:text-white transition-all shadow-xl hover:scale-110 active:scale-95"
                >
                    {showLeftPanel ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
                </button>
            </div>

            <div className="absolute top-6 right-6 z-[60] flex gap-2">
                <button
                    onClick={() => setShowRightPanel(!showRightPanel)}
                    className="p-3 bg-zinc-900/80 backdrop-blur-md border border-white/10 rounded-2xl text-zinc-400 hover:text-white transition-all shadow-xl hover:scale-110 active:scale-95"
                >
                    {showRightPanel ? <PanelRightClose size={18} /> : <PanelRight size={18} />}
                </button>
            </div>

            {/* CENTER: Real-time Tree Visualizer */}
            <div className="flex-1 relative h-full bg-[#050505] z-10 overflow-hidden">
                <TreeVisualizer
                    data={{ nodes, edges }}
                    progressivePlayback={false}
                />

                <ReasoningTerminal logs={thoughtStream} leftExpanded={showLeftPanel} rightExpanded={showRightPanel} />

                {nodes.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="text-center space-y-4 opacity-30">
                            <Brain size={60} className="mx-auto text-primary animate-pulse" />
                            <div className="text-xl font-light text-slate-500 italic">Synthesizing Thought Strata...</div>
                        </div>
                    </div>
                )}

                {/* Handoff Overlay */}
                <AnimatePresence>
                    {isComplete && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute bottom-48 left-1/2 -translate-x-1/2 bg-primary/90 text-white backdrop-blur-md px-10 py-6 rounded-3xl shadow-2xl border border-white/10 flex items-center gap-8 z-50"
                        >
                            <div className="flex flex-col">
                                <span className="text-[12px] font-black uppercase tracking-[0.3em] text-white/70">Path Finalized</span>
                                <span className="text-lg font-light">Navigating to lesson view in {countdown}s...</span>
                            </div>
                            <Sparkles className="text-secondary animate-pulse" size={32} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* RIGHT PANEL: Live Monitors */}
            <AnimatePresence>
                {showRightPanel && (
                    <motion.div
                        initial={{ x: 320 }}
                        animate={{ x: 0 }}
                        exit={{ x: 320 }}
                        className="w-80 h-full bg-zinc-900 border-l border-white/5 p-8 flex flex-col gap-8 z-20 overflow-y-auto shrink-0"
                    >
                        {/* CV Real-time Heartbeat */}
                        <div>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-secondary mb-6">Live Heartbeat (CV)</h3>
                            <div className="p-5 bg-white/[0.03] rounded-3xl border border-white/10 space-y-4">
                                <div className="flex items-center justify-between">
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Emotion</span>
                                    <span className="text-xs text-secondary font-black uppercase tracking-widest">{cvMetrics.emotion}</span>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Focused %</span>
                                    <div className="flex justify-between text-lg font-mono text-white">
                                        <span>{(cvMetrics.score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-secondary" style={{ width: `${cvMetrics.score * 100}%` }} />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                                    <div>
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Posture</span>
                                        <p className="text-xs font-mono text-white mt-1">{cvMetrics.posture}</p>
                                    </div>
                                    <div>
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Gaze</span>
                                        <p className="text-xs font-mono text-white mt-1">{cvMetrics.gaze}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* RL Policy Distribution */}
                        <div>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-6">Pedagogical Policy (RL)</h3>
                            <div className="p-5 bg-white/[0.03] rounded-3xl border border-white/10 space-y-4">
                                <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Action Distribution</span>
                                <div className="space-y-4">
                                    {Object.entries(rlPolicy).length > 0 ? (
                                        Object.entries(rlPolicy).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([action, weight]) => (
                                            <div key={action} className="space-y-1">
                                                <div className="flex justify-between text-[10px] font-bold text-zinc-400">
                                                    <span className="truncate w-40">{action}</span>
                                                    <span className="text-primary">{(weight * 100).toFixed(0)}%</span>
                                                </div>
                                                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                                    <div className="h-full bg-primary" style={{ width: `${weight * 100}%` }} />
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-[10px] text-zinc-500 italic py-4">Waiting for policy inference...</div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="mt-auto">
                            <div className="flex items-center gap-3 text-secondary mb-2">
                                <Zap size={14} className="animate-pulse" />
                                <span className="text-[10px] font-black uppercase tracking-widest">{status}</span>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default AgentDebugger;
