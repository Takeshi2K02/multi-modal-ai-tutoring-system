import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { motion } from 'framer-motion';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
    Activity, Brain, Camera, AlertTriangle, CheckCircle, Info, ChevronRight, Terminal
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const socket = io('http://localhost:8000');
const CV_BACKEND = "http://localhost:8000";

const AdminMonitor = () => {
    const [cvData, setCvData] = useState([]);
    const [rlData, setRlData] = useState(null);
    const [policyDistribution, setPolicyDistribution] = useState({});
    const [totSteps, setTotSteps] = useState([]);
    const [deviationAlert, setDeviationAlert] = useState(false);
    const [logs, setLogs] = useState([]);
    const [cameraActive, setCameraActive] = useState(false);

    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    // 1. WebSocket Listeners (Aligned with persistence.py)
    useEffect(() => {
        socket.on('cv_update', (data) => {
            setCvData((prev) => [...prev.slice(-80), {
                time: new Date(data.timestamp).toLocaleTimeString(),
                score: data.engagement_score,
                emotion: data.emotion,
                gaze: data.gaze,
                posture: data.posture,
                state: data.engagement_state
            }]);
            setLogs((prev) => [{ type: 'CV', data }, ...prev.slice(0, 49)]);
        });

        socket.on('rl_update', (data) => {
            setRlData(data);
            setLogs((prev) => [{ type: 'RL', data }, ...prev.slice(0, 49)]);
        });

        socket.on('tot_step', (data) => {
            setTotSteps((prev) => [...prev, data]);
            if (data.snapshot?.deviation_alert) {
                setDeviationAlert(true);
            }
            setLogs((prev) => [{ type: 'ToT_STEP', data }, ...prev.slice(0, 49)]);
        });

        socket.on('tot_final', (data) => {
            setLogs((prev) => [{ type: 'ToT_FINAL', data }, ...prev.slice(0, 49)]);
        });

        socket.on('policy_update', (data) => {
            setPolicyDistribution(data.distribution);
            setRlData(data.selected_action);
            setLogs((prev) => [{ type: 'POLICY', data }, ...prev.slice(0, 49)]);
        });

        return () => {
            socket.off('cv_update');
            socket.off('rl_update');
            socket.off('tot_step');
            socket.off('tot_final');
            socket.off('policy_update');
        };
    }, []);

    // 2. Camera Logic & Stream Reporting
    useEffect(() => {
        let stream = null;
        const startCamera = async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    setCameraActive(true);
                }
            } catch (err) {
                console.error("Camera Access Denied:", err);
            }
        };

        startCamera();

        const captureInterval = setInterval(() => {
            if (videoRef.current && canvasRef.current && cameraActive) {
                const canvas = canvasRef.current;
                const context = canvas.getContext('2d');
                context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

                const frame = canvas.toDataURL('image/jpeg', 0.5); // Compress for network

                fetch(`${CV_BACKEND}/api/engagement/track`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        frame: frame.split(',')[1], // Strip prefix
                        user_id: "alex_123",
                        material_id: "unit_1_calculus"
                    })
                }).catch(e => console.warn("CV Backend Offline"));
            }
        }, 1500);

        return () => {
            clearInterval(captureInterval);
            if (stream) stream.getTracks().forEach(t => t.stop());
        };
    }, [cameraActive]);

    return (
        <div className="h-full overflow-y-auto bg-edu-bg-light dark:bg-edu-bg-dark text-edu-text-light dark:text-edu-text-dark p-6 lg:p-12 font-sans selection:bg-primary/30 transition-colors duration-300 custom-scrollbar">
            {/* Wrapper for Max Width (Global spacer in App.jsx handles top clearance) */}
            <div className="max-w-[1600px] mx-auto">
                <header className="mb-12 flex flex-col md:flex-row justify-between items-start md:items-center bg-white/80 dark:bg-[#1E293B]/15 backdrop-blur-3xl p-8 rounded-[40px] border border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl relative overflow-hidden group transition-colors duration-300">
                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                    <div className="flex items-center gap-6 relative z-10">
                        <div className="p-4 bg-primary/10 rounded-3xl border border-primary/20 shadow-[0_0_20px_rgba(99,102,241,0.2)]">
                            <Brain className="w-10 h-10 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-light tracking-tight text-edu-text-light dark:text-white mb-1 transition-colors">
                                Live Monitor <span className="text-primary font-medium">Observability</span>
                            </h1>
                            <p className="text-sm text-zinc-500 dark:text-slate-500 font-light tracking-wide transition-colors">Real-time system orchestration & multi-modal telemetry</p>
                        </div>
                    </div>
                    <div className={cn(
                        "mt-6 md:mt-0 flex items-center gap-3 px-6 py-3 rounded-full border transition-all duration-700 relative z-10",
                        deviationAlert ? "bg-[#F07167]/10 border-[#F07167]/50 text-[#F07167] shadow-[0_0_15px_rgba(240,113,103,0.2)] animate-pulse" : "bg-[#00AFB9]/5 border-[#00AFB9]/20 text-[#00AFB9]"
                    )}>
                        <div className={cn("w-2 h-2 rounded-full", deviationAlert ? "bg-[#F07167] shadow-[0_0_8px_#F07167]" : "bg-[#00AFB9] shadow-[0_0_8px_#00AFB9]")} />
                        <span className="font-bold uppercase tracking-[0.2em] text-[10px]">
                            {deviationAlert ? "Baseline Deviation Triggered" : "System Stable"}
                        </span>
                    </div>
                </header>

                {/* Hidden Canvas for Frame Processing */}
                <canvas ref={canvasRef} width="320" height="240" className="hidden" />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* CV - Affect Sensing Panel (Premium Glass Card) */}
                    <div className="bg-white/80 dark:bg-[#1E293B]/80 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-[#90E0EF]/10 overflow-hidden shadow-2xl transition-all hover:bg-white dark:hover:bg-[#1E293B]/90">
                        <div className="p-6 border-b border-edu-border-light dark:border-[#90E0EF]/10 flex items-center justify-between bg-white dark:bg-[#1E293B]/20">
                            <div className="flex items-center gap-3">
                                <Camera className="w-5 h-5 text-primary" />
                                <span className="font-bold uppercase text-[10px] tracking-[0.2em] text-zinc-500 dark:text-slate-400">Live Affect Sensing (CV)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={cn(
                                    "w-2 h-2 rounded-full transition-all duration-500",
                                    cameraActive ? "bg-primary shadow-[0_0_12px_#0077B6] animate-pulse" : "bg-zinc-300 dark:bg-slate-700"
                                )} />
                                <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 dark:text-slate-500">{cameraActive ? 'Active' : 'Offline'}</span>
                            </div>
                        </div>
                        <div className="p-8">
                            <div className="flex flex-col items-center gap-8 mb-10">
                                {/* CAMERA PREVIEW - CENTERED */}
                                <div className="relative w-full max-w-[360px] h-[240px] bg-black rounded-[32px] border border-edu-border-light dark:border-white/10 overflow-hidden shadow-[inset_0_0_30px_rgba(0,0,0,0.9)] group">
                                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover -scale-x-100 transition-opacity duration-1000" />
                                    <div className="absolute inset-0 bg-primary/10 mix-blend-overlay opacity-50" />
                                    {!cameraActive && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                            <Camera className="w-8 h-8 text-zinc-700 dark:text-slate-700 animate-pulse" />
                                            <span className="text-[10px] text-zinc-500 dark:text-slate-500 uppercase font-black tracking-tighter">Stream Offline</span>
                                        </div>
                                    )}
                                </div>

                                {/* TELEMETRY DATA - BELOW CAMERA */}
                                <div className="grid grid-cols-2 w-full gap-4 pt-6 border-t border-edu-border-light dark:border-white/5">
                                    <div className="text-center border-r border-edu-border-light dark:border-white/5">
                                        <p className="text-[9px] text-zinc-500 dark:text-slate-500 uppercase font-bold tracking-[0.2em] mb-2">Emotion</p>
                                        <p className="text-3xl font-light text-edu-text-light dark:text-white capitalize tracking-wide">
                                            {cvData[cvData.length - 1]?.emotion || <span className="opacity-20 text-sm italic">Analyzing...</span>}
                                        </p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-[9px] text-zinc-500 dark:text-slate-500 uppercase font-bold tracking-[0.2em] mb-2">Confidence</p>
                                        <p className="text-4xl font-mono font-light text-primary">
                                            {cvData[cvData.length - 1]?.score !== undefined ? `${(cvData[cvData.length - 1].score * 100).toFixed(0)}%` : '0%'}
                                        </p>
                                    </div>
                                </div>

                                {/* REFINED: DETAILED METRICS LAYOUT */}
                                <div className="w-full space-y-4 pt-4 border-t border-edu-border-light dark:border-white/5">
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="text-center border-r border-edu-border-light dark:border-white/5">
                                            <p className="text-[8px] text-zinc-400 dark:text-slate-600 uppercase font-bold tracking-widest mb-1">Gaze</p>
                                            <p className="text-sm text-edu-text-light dark:text-zinc-300 capitalize">
                                                {cvData[cvData.length - 1]?.gaze || '---'}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-[8px] text-zinc-400 dark:text-slate-600 uppercase font-bold tracking-widest mb-1">State</p>
                                            <p className="text-sm text-edu-text-light dark:text-zinc-300 capitalize truncate">
                                                {cvData[cvData.length - 1]?.state?.replace('_', ' ') || '---'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-center pt-2 border-t border-edu-border-light/30 dark:border-white/5">
                                        <p className="text-[8px] text-zinc-400 dark:text-slate-600 uppercase font-bold tracking-widest mb-1">Posture</p>
                                        <p className="text-sm text-edu-text-light dark:text-zinc-300 capitalize">
                                            {cvData[cvData.length - 1]?.posture?.replace('_', ' ') || '---'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="h-40 w-full opacity-60">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={cvData}>
                                        <XAxis dataKey="time" hide />
                                        <YAxis domain={[0, 1]} hide />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: 'rgba(3, 4, 94, 0.8)', borderRadius: '16px', border: '1px solid rgba(144, 224, 239, 0.1)', backdropFilter: 'blur(12px)' }}
                                            itemStyle={{ color: '#0077B6', fontSize: '12px', fontWeight: 'bold' }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="score"
                                            stroke="#48CAE4"
                                            strokeWidth={3}
                                            dot={false}
                                            animationDuration={300}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* RL - Pedagogical Strategy Panel (Premium Glass Card) */}
                    <div className="bg-white/80 dark:bg-[#1E293B]/15 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-[#90E0EF]/10 overflow-hidden shadow-2xl transition-all hover:bg-white dark:hover:bg-[#1E293B]/30">
                        <div className="p-6 border-b border-edu-border-light dark:border-[#90E0EF]/10 flex items-center gap-3 bg-white dark:bg-[#1E293B]/40">
                            <Activity className="w-5 h-5 text-secondary" />
                            <span className="font-bold uppercase text-[10px] tracking-[0.2em] text-zinc-500 dark:text-slate-400">Pedagogical Policy (RL)</span>
                        </div>
                        <div className="p-8 flex flex-col justify-center h-full min-h-[400px]">
                            {rlData ? (
                                <div className="space-y-10">
                                    <div>
                                        <p className="text-[10px] text-zinc-500 dark:text-slate-500 uppercase font-bold tracking-[0.15em] mb-4">Neural Strategy</p>
                                        <div className="bg-edu-bg-light/50 dark:bg-white/[0.03] p-6 rounded-[32px] border border-edu-border-light dark:border-white/10 relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/5 blur-[40px] rounded-full" />
                                            <p className="text-2xl font-light text-edu-text-light dark:text-white mb-3 relative z-10">{rlData.policy_name}</p>
                                            <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-slate-500 font-light italic relative z-10">
                                                <Info size={14} className="text-secondary" />
                                                <span>{rlData.reasoning || 'Heuristic calculation active'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="bg-edu-bg-light/50 dark:bg-white/[0.02] p-6 rounded-3xl border border-edu-border-light dark:border-white/5 text-center transition-all hover:bg-edu-surface-light dark:hover:bg-white/[0.04]">
                                            <p className="text-[9px] text-zinc-400 dark:text-slate-600 uppercase font-black tracking-widest mb-2">Target Action</p>
                                            <p className="text-3xl font-mono font-light text-secondary">{rlData.action_id}</p>
                                        </div>
                                        <div className="bg-edu-bg-light/50 dark:bg-white/[0.02] p-6 rounded-3xl border border-edu-border-light dark:border-white/5 text-center transition-all hover:bg-edu-surface-light dark:hover:bg-white/[0.04]">
                                            <p className="text-[9px] text-zinc-400 dark:text-slate-600 uppercase font-black tracking-widest mb-2">Confidence</p>
                                            <p className="text-3xl font-mono font-light text-secondary">{(rlData.confidence * 100).toFixed(0)}%</p>
                                        </div>
                                    </div>

                                    {/* Real-time Distribution Chart (Project ID: 25-26J-130) */}
                                    <div className="pt-6 border-t border-edu-border-light dark:border-white/5">
                                        <p className="text-[10px] text-zinc-500 dark:text-slate-500 uppercase font-bold tracking-[0.15em] mb-4">Action Distribution</p>
                                        <div className="space-y-4">
                                            {Object.entries(policyDistribution).map(([name, weight]) => (
                                                <div key={name} className="space-y-1">
                                                    <div className="flex justify-between text-[10px] uppercase tracking-tighter">
                                                        <span className={cn(
                                                            "transition-colors duration-500",
                                                            name === rlData.policy_name ? "text-secondary font-black" : "text-zinc-400 dark:text-slate-600"
                                                        )}>
                                                            {name}
                                                        </span>
                                                        <span className="font-mono text-zinc-400">{(weight * 100).toFixed(0)}%</span>
                                                    </div>
                                                    <div className="h-1 rounded-full bg-zinc-100 dark:bg-white/5 overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${weight * 100}%` }}
                                                            transition={{ duration: 0.5, ease: "easeOut" }}
                                                            className={cn(
                                                                "h-full rounded-full transition-colors duration-500",
                                                                name === rlData.policy_name ? "bg-secondary shadow-[0_0_10px_#00AFB9]" : "bg-primary/20"
                                                            )}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-slate-600 py-12">
                                    <Activity className="w-16 h-16 mb-6 opacity-10 animate-pulse" />
                                    <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-30">Waiting for Signal...</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ToT - Tree of Thought Trace (Premium Glass Card) */}
                    <div className="bg-white/80 dark:bg-[#1E293B]/15 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-[#90E0EF]/10 overflow-hidden shadow-2xl lg:row-span-2 flex flex-col transition-colors duration-300">
                        <div className="p-6 border-b border-edu-border-light dark:border-[#90E0EF]/10 flex items-center gap-3 bg-white dark:bg-[#1E293B]/10">
                            <Brain className="w-5 h-5 text-accent" />
                            <span className="font-bold uppercase text-[10px] tracking-[0.2em] text-zinc-500 dark:text-slate-400">Agentic Reasoning (ToT)</span>
                        </div>
                        <div className="p-8 flex-1 overflow-y-auto custom-scrollbar">
                            <div className="space-y-6">
                                {totSteps.length > 0 ? totSteps.map((step, idx) => (
                                    <div key={idx} className="relative pl-8 border-l border-primary/10 pb-6 group">
                                        <div className="absolute left-[-5px] top-0 w-2.5 h-2.5 rounded-full bg-primary shadow-[0_0_15px_#0077B6] transition-transform group-hover:scale-125" />
                                        <div className="bg-edu-bg-light/50 dark:bg-white/[0.02] p-5 rounded-[32px] border border-edu-border-light dark:border-white/5 hover:bg-edu-surface-light dark:hover:bg-white/[0.05] transition-all duration-500 hover:translate-x-1">
                                            <div className="flex justify-between items-center mb-3">
                                                <span className="text-[9px] font-black uppercase text-primary tracking-widest">{step.step.replace('_', ' ')}</span>
                                                {step.depth && <span className="text-[9px] bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full text-primary font-bold">DEPTH {step.depth}</span>}
                                            </div>
                                            {step.step === 'retrieve_context' && (
                                                <p className="text-xs text-zinc-600 dark:text-slate-300 font-light leading-relaxed">Initialized root for query: <span className="text-edu-text-light dark:text-white font-medium">"{step.query}"</span></p>
                                            )}
                                            {step.step === 'expand_frontier' && (
                                                <p className="text-xs text-zinc-600 dark:text-slate-300 font-light">Expanded <span className="text-primary font-black">{step.new_nodes_count}</span> candidate trajectories.</p>
                                            )}
                                            {step.step === 'evaluate_frontier' && (
                                                <div className="mt-3 space-y-2">
                                                    <p className="text-[9px] text-zinc-400 dark:text-slate-600 font-bold uppercase tracking-widest mb-2">Node Scoring Vector</p>
                                                    <div className="flex gap-1.5 h-1.5">
                                                        {step.scores.map((s, i) => (
                                                            <div key={i} className="flex-1 rounded-full bg-zinc-200 dark:bg-slate-900 border border-edu-border-light dark:border-white/5 overflow-hidden">
                                                                <div className="h-full bg-gradient-to-r from-primary to-accent" style={{ width: `${s * 100}%` }} />
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )) : (
                                    <div className="text-center py-24 text-slate-600">
                                        <div className="w-16 h-16 bg-white/[0.02] rounded-full flex items-center justify-center mx-auto mb-6 border border-white/5">
                                            <ChevronRight className="w-8 h-8 opacity-10" />
                                        </div>
                                        <p className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-30">Inference Idle</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* System Logs Feed (Integrated Terminal View) */}
                    <div className="lg:col-span-2 bg-white/80 dark:bg-[#1E293B]/15 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-[#90E0EF]/10 overflow-hidden shadow-2xl flex flex-col min-h-[400px]">
                        <div className="p-6 border-b border-edu-border-light dark:border-[#90E0EF]/10 flex items-center justify-between bg-white dark:bg-[#1E293B]/20">
                            <div className="flex items-center gap-3">
                                <Terminal className="w-5 h-5 text-zinc-500 dark:text-slate-500" />
                                <span className="font-bold uppercase text-[10px] tracking-[0.2em] text-zinc-500 dark:text-slate-400">System Trace Engine</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse shadow-[0_0_8px_#00AFB9]" />
                                <span className="text-[9px] font-bold text-zinc-400 dark:text-slate-600 uppercase tracking-widest leading-none">Live Socket</span>
                            </div>
                        </div>
                        <div className="p-4 flex-1 h-[320px] overflow-y-auto bg-edu-bg-light/80 dark:bg-black/40 font-mono text-[11px] custom-scrollbar selection:bg-primary/40">
                            {logs.map((log, i) => (
                                <div key={i} className="px-5 py-3 border-b border-white/[0.02] hover:bg-white/[0.03] transition-colors group flex items-start gap-4">
                                    <span className={cn(
                                        "shrink-0 px-2 py-0.5 rounded text-[8px] font-black tracking-widest",
                                        log.type === 'CV' ? "bg-primary/10 text-primary border border-primary/20" :
                                            log.type === 'RL' || log.type === 'POLICY' ? "bg-secondary/10 text-secondary border border-secondary/20" : "bg-accent/10 text-accent border border-accent/20"
                                    )}>
                                        {log.type}
                                    </span>
                                    <span className="text-zinc-400 dark:text-slate-700 shrink-0 font-bold">{new Date().toLocaleTimeString()}</span>
                                    <span className="text-zinc-600 dark:text-slate-400 group-hover:text-edu-text-light dark:group-hover:text-white break-all font-light leading-relaxed">
                                        {log.type === 'CV' ? (
                                            <span className="text-primary/80">
                                                Emotion: <span className="text-primary font-bold">{log.data.emotion}</span> |
                                                Score: <span className="text-primary font-bold">{log.data.engagement_score.toFixed(2)}</span> |
                                                Gaze: <span className="text-primary font-bold">{log.data.gaze}</span> |
                                                Posture: <span className="text-primary font-bold">{log.data.posture}</span> |
                                                State: <span className="text-primary font-bold">{log.data.engagement_state}</span>
                                            </span>
                                        ) : JSON.stringify(log.data)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 4px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
                @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            `}</style>
        </div>
    );
};

export default AdminMonitor;
