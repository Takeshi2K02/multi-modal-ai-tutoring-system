import React from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

const SignalCard = ({ title, source, children, color }) => (
    <div className={clsx("bg-white/80 backdrop-blur-md rounded-xl p-4 border shadow-sm", color)}>
        <div className="flex items-center justify-between mb-3 border-b border-black/5 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">{title}</h3>
            <span className="text-[10px] font-mono opacity-60">SOURCE: {source}</span>
        </div>
        <div className="space-y-2">
            {children}
        </div>
    </div>
);

const Field = ({ label, value, type = "text" }) => (
    <div className="flex justify-between items-start text-sm">
        <span className="text-slate-500 font-medium text-xs uppercase mt-0.5">{label}</span>
        {type === "badge" ? (
            <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-white uppercase">
                {value}
            </span>
        ) : (
            <span className="font-mono text-slate-700 text-xs text-right max-w-[60%] break-words leading-tight">
                {typeof value === 'object' ? JSON.stringify(value) : value}
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
            className="absolute top-6 right-6 w-80 flex flex-col gap-4 z-40 pointer-events-none"
        >
            {/* Note for Viva Panel */}
            <div className="bg-slate-900/90 text-white px-4 py-2 rounded-lg text-xs font-medium text-center shadow-lg backdrop-blur pointer-events-auto">
                RL decides <b>WHAT</b> • Agent decides <b>HOW</b>
            </div>

            {/* CV Signal Card */}
            {cv && (
                <div className="pointer-events-auto">
                    <SignalCard title="Perception State" source="CV Model" color="border-emerald-200 shadow-emerald-100">
                        <Field label="Emotion" value={cv.emotion} type="badge" />
                        <Field label="Engagement State" value={cv.engagement_state} />
                        <Field label="Engagement Score" value={cv.engagement_score} />
                        <Field label="Gaze" value={cv.gaze} />
                        <Field label="Posture" value={cv.posture} />
                        <Field label="Timestamp" value={cv.timestamp} />
                    </SignalCard>
                </div>
            )}

            {/* RL Policy Card */}
            {rl_hint && (
                <div className="pointer-events-auto">
                    <SignalCard title="Usage Policy" source="RL Engine" color="border-indigo-200 shadow-indigo-100">
                        <Field label="Policy Action" value={rl_hint.action_id} type="badge" />
                        <div className="mt-1 p-2 bg-indigo-50 rounded border border-indigo-100 text-indigo-900 text-xs font-semibold">
                            "{rl_hint.policy_name || "Unknown Policy"}"
                        </div>
                        <Field label="Confidence" value={rl_hint.confidence} />
                        <Field label="Reasoning" value={rl_hint.reasoning} />
                    </SignalCard>
                </div>
            )}
        </motion.div>
    );
};

export default SignalsPanel;
