import React from 'react';
import useSWR from 'swr';
import { motion } from 'framer-motion';
import {
    Database,
    Activity,
    BrainCircuit,
    User,
    ChevronRight,
    TrendingUp,
    Clock,
    ShieldCheck,
    Zap
} from 'lucide-react';
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    AreaChart,
    Area
} from 'recharts';
import { fetcher, API_BASE_URL } from '../services/api';

/**
 * DataDashboard Component
 * 
 * DESIGN RATIONALE:
 * 1. Zen-mode Aesthetic: Deep black (#000000) background for maximum focus.
 * 2. Premium Glassmorphism: backdrop-blur-3xl and thin white borders.
 * 3. Future-proof UI: User preferences designed as clickable-style cards.
 */
const DataDashboard = () => {
    const { data: analytics, error } = useSWR(`${API_BASE_URL}/api/analytics/historical?user_id=alex_123`, fetcher);

    const cvStats = analytics?.cv_stats || {};
    const rlStats = analytics?.rl_stats || {};
    const preferences = analytics?.preferences || {};

    // Mock data for sparklines trend (Last 7 Sessions)
    const engagementTrend = [
        { name: 'S1', score: 0.65 },
        { name: 'S2', score: 0.72 },
        { name: 'S3', score: 0.68 },
        { name: 'S4', score: 0.85 },
        { name: 'S5', score: 0.78 },
        { name: 'S6', score: 0.92 },
        { name: 'S7', score: analytics?.cv_stats?.average_engagement || 0.8 }
    ];

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-black">
                <p className="text-rose-400 font-light tracking-widest uppercase text-sm">Synchronizing Intelligence Failed</p>
            </div>
        );
    }

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark font-sans selection:bg-primary/30 overflow-y-auto custom-scrollbar transition-colors">
            <div className="max-w-[1600px] mx-auto px-6 py-12 relative z-10">

                {/* Header: Zen Minimalism */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="mb-16"
                >
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-[0_0_20px_rgba(99,102,241,0.15)] transition-all">
                            <Database className="text-primary" size={20} />
                        </div>
                        <span className="text-[10px] uppercase font-bold tracking-[0.3em] text-zinc-400 dark:text-slate-500 underline decoration-primary/30 underline-offset-8 transition-colors">Data Center</span>
                    </div>
                    <h1 className="text-5xl md:text-6xl font-light tracking-tight text-edu-text-light dark:text-white leading-tight transition-colors">
                        Cognitive <br />
                        <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-400 to-primary animate-gradient-x">
                            Historical Analytics
                        </span>
                    </h1>
                </motion.div>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

                    {/* LEFT COLUMN: Preferences & RL Distribution (4 Cols) */}
                    <div className="xl:col-span-4 space-y-8">
                        {/* USER PREFERENCES - GLASS CARDS */}
                        <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 overflow-hidden p-8 shadow-sm dark:shadow-2xl relative group transition-all">
                            <div className="flex items-center justify-between mb-8">
                                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 flex items-center gap-3 transition-colors">
                                    <User size={14} className="text-primary" />
                                    Student Profile
                                </h3>
                                <div className="px-3 py-1 bg-primary/10 border border-primary/20 rounded-full transition-colors">
                                    <span className="text-[9px] font-black tracking-tighter text-primary uppercase">Immutable</span>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {[
                                    { label: 'Primary Modality', value: preferences?.learning_style, icon: <Zap size={14} /> },
                                    { label: 'Scaffolding Bias', value: preferences?.difficulty_bias, icon: <ShieldCheck size={14} /> },
                                    { label: 'Session Velocity', value: preferences?.session_length_pref, icon: <Clock size={14} /> },
                                    { label: 'Agent Persona', value: preferences?.tone_preference, icon: <TrendingUp size={14} /> },
                                ].map((item, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-4 bg-zinc-50 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/5 rounded-2xl transition-all hover:bg-zinc-100 dark:hover:bg-white/[0.05] hover:border-primary/20 dark:hover:border-white/10 cursor-not-allowed group/item">
                                        <div className="flex items-center gap-4">
                                            <div className="w-8 h-8 rounded-xl bg-white dark:bg-black/40 shadow-inner flex items-center justify-center text-zinc-400 dark:text-slate-500 group-hover/item:text-primary transition-colors">
                                                {item.icon}
                                            </div>
                                            <div>
                                                <p className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-bold tracking-wider mb-0.5 transition-colors">{item.label}</p>
                                                <p className="text-sm text-edu-text-light dark:text-white font-light transition-colors">{item.value || 'Unset'}</p>
                                            </div>
                                        </div>
                                        <ChevronRight size={14} className="text-zinc-300 dark:text-slate-700 opacity-0 group-hover/item:opacity-100 transition-all -translate-x-2 group-hover/item:translate-x-0" />
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* RL ACTION FREQUENCY */}
                        <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 overflow-hidden p-8 shadow-sm dark:shadow-2xl transition-all">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 mb-8 flex items-center gap-3 transition-colors">
                                <BrainCircuit size={14} className="text-primary" />
                                RL Policy Distribution
                            </h3>
                            <div className="space-y-6">
                                {Object.entries(rlStats?.action_distribution || {}).length > 0 ? (
                                    Object.entries(rlStats.action_distribution).map(([action, count], idx) => (
                                        <div key={idx} className="space-y-2">
                                            <div className="flex justify-between items-end">
                                                <span className="text-[11px] text-zinc-600 dark:text-slate-300 font-medium tracking-tight transition-colors">{action}</span>
                                                <span className="text-[11px] font-mono text-primary transition-colors">{count} inst</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-zinc-100 dark:bg-white/5 rounded-full overflow-hidden transition-colors">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${(count / (rlStats.total_decisions || 1)) * 100}%` }}
                                                    className="h-full bg-gradient-to-r from-primary to-accent"
                                                />
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="py-12 text-center">
                                        <p className="text-slate-600 text-xs italic">No longitudinal data maps available.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN: CV Analytics & Sparklines (8 Cols) */}
                    <div className="xl:col-span-8 flex flex-col gap-8">

                        {/* CV ANALYTICS OVERVIEW */}
                        <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 shadow-sm dark:shadow-2xl flex-1 transition-all">
                            <div className="flex items-center justify-between mb-12">
                                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 flex items-center gap-3 transition-colors">
                                    <Activity size={14} className="text-primary" />
                                    Affective Intelligence Logs
                                </h3>
                                <div className="text-[10px] text-zinc-400 dark:text-slate-500 tracking-widest transition-colors">WINDOW: 24 HOURS</div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                                <div className="p-8 bg-zinc-50 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/5 rounded-[32px] transition-colors">
                                    <p className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-bold tracking-[0.2em] mb-4 transition-colors">AVG Engagement</p>
                                    <p className="text-6xl font-light text-edu-text-light dark:text-white tracking-tighter transition-colors">
                                        {cvStats?.average_engagement || '0.00'}
                                    </p>
                                    <div className="mt-4 flex items-center gap-2 text-secondary">
                                        <TrendingUp size={14} />
                                        <span className="text-[10px] font-bold">+12.4% from avg</span>
                                    </div>
                                </div>
                                <div className="md:col-span-2 p-8 bg-zinc-50 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/5 rounded-[32px] overflow-hidden transition-colors">
                                    <p className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-bold tracking-[0.2em] mb-8 transition-colors">Engagement Stability</p>
                                    <div className="h-40 w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={engagementTrend}>
                                                <defs>
                                                    <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="var(--edu-primary)" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="var(--edu-primary)" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: 'var(--edu-surface)',
                                                        border: '1px solid var(--edu-border)',
                                                        borderRadius: '16px',
                                                        color: 'var(--edu-text)'
                                                    }}
                                                    itemStyle={{ color: 'var(--edu-primary)' }}
                                                />
                                                <Area
                                                    type="monotone"
                                                    dataKey="score"
                                                    stroke="var(--edu-primary)"
                                                    strokeWidth={3}
                                                    fillOpacity={1}
                                                    fill="url(#colorEngagement)"
                                                    animationDuration={2000}
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                {Object.entries(cvStats?.dominant_emotions || {}).length > 0 ? (
                                    Object.entries(cvStats.dominant_emotions).map(([emo, freq], idx) => (
                                        <div key={idx} className="p-6 bg-white dark:bg-white/[0.01] border border-edu-border-light dark:border-white/5 rounded-3xl text-center transition-all hover:bg-zinc-50 dark:hover:bg-white/[0.03] shadow-sm dark:shadow-none">
                                            <p className="text-xs text-edu-text-light dark:text-white capitalize font-medium mb-1 transition-colors">{emo}</p>
                                            <p className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-black tracking-widest transition-colors">{freq} Hits</p>
                                        </div>
                                    ))
                                ) : (
                                    <div className="col-span-full p-8 text-center text-slate-600 italic text-sm">No significant emotive signatures recorded.</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Disclaimer */}
                <div className="mt-20 text-center opacity-40 hover:opacity-100 transition-opacity duration-1000">
                    <p className="text-[10px] text-zinc-400 dark:text-slate-400 uppercase font-bold tracking-[0.4em] transition-colors">Integrated Intelligence Data Center v1.0.4</p>
                </div>

            </div>
        </div>
    );
};

export default DataDashboard;
