import React from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

const SignalCard = ({ title, source, children, color, icon: Icon }) => (
    <div className={clsx("bg-edu-surface-light dark:bg-white/[0.03] backdrop-blur-xl rounded-[32px] p-6 border-l-4 shadow-2xl transition-all duration-500 hover:bg-edu-surface-light/50 dark:hover:bg-white/[0.05]", color)}>
        <div className="flex items-center justify-between mb-6 border-b border-edu-border-light dark:border-white/5 pb-4">
            <div className="flex items-center gap-3">
                {Icon && <Icon size={14} className="opacity-50 text-edu-text-light dark:text-white" />}
                <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 dark:text-slate-400">{title}</h3>
            </div>
            <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse shadow-[0_0_8px_#10b981]" />
                <span className="text-[9px] font-black tracking-widest text-zinc-400 dark:text-slate-600 uppercase">Live</span>
            </div>
        </div>
        <div className="space-y-4">
            {children}
        </div>
        <div className="mt-6 pt-4 border-t border-edu-border-light dark:border-white/5 flex justify-between items-center">
            <span className="text-[8px] font-black text-zinc-400 dark:text-slate-700 uppercase tracking-widest">Telemetry Source</span>
            <span className="text-[8px] font-mono text-zinc-500 dark:text-slate-500 uppercase">{source}</span>
        </div>
    </div>
);

const Field = ({ label, value, type = "text", accent }) => (
    <div className="flex justify-between items-center text-sm group">
        <span className="text-zinc-500 dark:text-slate-500 font-bold text-[9px] uppercase tracking-widest group-hover:text-primary dark:group-hover:text-slate-300 transition-colors">{label}</span>
        {type === "badge" ? (
            <span className={clsx("inline-flex px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-tighter shadow-lg", accent || "bg-primary/10 dark:bg-white/10 text-primary dark:text-white")}>
                {value}
            </span>
        ) : (
            <span className="font-mono text-edu-text-light dark:text-white text-[10px] text-right font-light tracking-tight group-hover:text-primary transition-colors">
                {typeof value === 'number' ? value.toFixed(2) : (typeof value === 'object' ? JSON.stringify(value) : value)}
            </span>
        )}
    </div>
);

const SignalsPanel = ({ data }) => {
    if (!data) return null;

    const { cv, rl_hint } = data;

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="absolute top-8 right-8 w-80 flex flex-col gap-6 z-40 pointer-events-none"
        >
            {/* Legend / Status Overlay */}
            <div className="bg-edu-surface-light/80 dark:bg-black/60 border border-edu-border-light dark:border-white/10 text-zinc-500 dark:text-slate-400 px-6 py-3 rounded-full text-[9px] font-black uppercase tracking-[0.3em] text-center backdrop-blur-3xl shadow-2xl pointer-events-auto border-b-2 border-b-primary/50 transition-colors">
                Decision Core <span className="text-primary mx-2">|</span> Engine Latency: <span className="text-secondary">Stable</span>
            </div>

            {/* CV Signal Card */}
            {cv && (
                <div className="pointer-events-auto">
                    <SignalCard title="Perception" source="CV_ENGINE" color="border-secondary/40" icon={Camera}>
                        <Field label="Affect" value={cv.emotion} type="badge" accent="bg-secondary/20 text-secondary border border-secondary/30" />
                        <Field label="Engagement" value={cv.engagement_score} />
                        <Field label="Gaze Focus" value={cv.gaze} />
                        <Field label="Posture" value={cv.posture} />
                        <div className="pt-2">
                            <div className="h-1 w-full bg-zinc-100 dark:bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-secondary"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${(cv.engagement_score || 0.5) * 100}%` }}
                                />
                            </div>
                        </div>
                    </SignalCard>
                </div>
            )}

            {/* RL Policy Card */}
            {rl_hint && (
                <div className="pointer-events-auto">
                    <SignalCard title="Usage Policy" source="RL_ENGINE" color="border-primary/40" icon={Bot}>
                        <Field label="Policy ID" value={rl_hint.action_id} type="badge" accent="bg-primary/20 text-primary border border-primary/30" />
                        <div className="p-4 bg-zinc-50 dark:bg-white/[0.02] rounded-2xl border border-edu-border-light dark:border-white/5 mt-2 transition-all hover:bg-zinc-100 dark:hover:bg-white/[0.04]">
                            <span className="text-[8px] font-black text-primary/60 dark:text-primary/60 uppercase tracking-widest block mb-2">Decided Intervention</span>
                            <p className="text-xs font-light text-edu-text-light dark:text-slate-200 leading-relaxed italic">
                                "{rl_hint.policy_name || "Observing student patterns..."}"
                            </p>
                        </div>
                        <Field label="Confidence" value={rl_hint.confidence} />
                    </SignalCard>
                </div>
            )}
        </motion.div>
    );
};

export default SignalsPanel;
