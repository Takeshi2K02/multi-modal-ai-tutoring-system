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
    Zap,
    History,
    Sparkles,
    FileText,
    Target,
    HeartPulse
} from 'lucide-react';
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    AreaChart,
    Area,
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    ReferenceLine
} from 'recharts';
import { fetcher, API_BASE_URL } from '../services/api';

const DataDashboard = () => {
    const { data: analytics, error } = useSWR(`${API_BASE_URL}/api/analytics/profile/alex_123`, fetcher, {
        refreshInterval: 5000
    });

    const profile = analytics?.profile || { primary_modality: 'Visual', scaffolding_bias: '+0.15', radar_data: [] };
    const affective = analytics?.affective || { avg_engagement: 0.68, engagement_trend: [], emotions: [] };
    const intervention = analytics?.intervention || { success_rate: 0, recent_swaps: [], policy_distribution: [] };
    const masteryData = analytics?.mastery_data || [];

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-black">
                <p className="text-rose-400 font-light tracking-widest uppercase text-sm">Intelligence Sync Failed</p>
            </div>
        );
    }

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark font-sans selection:bg-primary/30 overflow-y-auto custom-scrollbar transition-colors">
            <div className="max-w-[1600px] mx-auto px-6 py-12 relative z-10">

                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8"
                >
                    <div>
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-[0_0_20px_rgba(99,102,241,0.15)]">
                                <Database className="text-primary" size={20} />
                            </div>
                            <span className="text-[10px] uppercase font-bold tracking-[0.3em] text-zinc-400 dark:text-slate-500 underline decoration-primary/30 underline-offset-8">Intelligence Registry</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-light tracking-tight text-edu-text-light dark:text-white leading-tight">
                            Cognitive <br />
                            <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-400 to-primary animate-gradient-x">
                                Historical Audit
                            </span>
                        </h1>
                    </div>
                    <div className="p-6 bg-white/5 border border-white/10 rounded-[32px] backdrop-blur-3xl hidden lg:block">
                        <div className="flex items-center gap-6">
                            <div className="text-right">
                                <p className="text-[10px] uppercase font-black text-zinc-500 tracking-widest">System Health</p>
                                <p className="text-sm font-medium text-secondary">Optimal Performance</p>
                            </div>
                            <div className="w-12 h-12 rounded-full border-2 border-secondary/20 border-t-secondary animate-spin" />
                        </div>
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

                    {/* MODULE 1: STUDENT PROFILE (4 Cols) */}
                    <div className="xl:col-span-4 space-y-8">
                        <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 shadow-sm dark:shadow-2xl relative group overflow-hidden">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 mb-8 flex items-center gap-3">
                                <User size={14} className="text-primary" />
                                Student Profile
                            </h3>

                            <div className="space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-white/5 border border-white/5 rounded-2xl">
                                        <p className="text-[9px] uppercase font-black text-zinc-500 mb-1">Primary Modality</p>
                                        <p className="text-lg font-light text-white">{profile.primary_modality}</p>
                                    </div>
                                    <div className="p-4 bg-white/5 border border-white/5 rounded-2xl">
                                        <p className="text-[9px] uppercase font-black text-zinc-500 mb-1">Scaffolding Bias</p>
                                        <p className="text-lg font-light text-secondary">{profile.scaffolding_bias}</p>
                                    </div>
                                </div>

                                <div className="h-[240px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={profile.radar_data}>
                                            <PolarGrid stroke="rgba(255,255,255,0.05)" />
                                            <PolarAngleAxis dataKey="subject" tick={{ fill: "#64748b", fontSize: 9, fontWeight: 700 }} />
                                            <Radar name="Preference" dataKey="value" stroke="var(--edu-primary)" fill="var(--edu-primary)" fillOpacity={0.4} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="space-y-4 pt-4 border-t border-white/5">
                                    <div className="flex items-center justify-between">
                                        <p className="text-[10px] uppercase font-black text-zinc-500 tracking-widest">Mastery Hub</p>
                                        <span className="text-[9px] text-primary font-bold">Sync Active</span>
                                    </div>
                                    <div className="space-y-2">
                                        {masteryData.map((m, i) => (
                                            <div key={i} className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl flex items-center justify-between group hover:border-primary/30 transition-all">
                                                <div>
                                                    <p className="text-sm font-medium text-white">{m.topic}</p>
                                                    <p className="text-[9px] text-zinc-500 uppercase font-bold tracking-tighter">{m.source}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-sm font-black text-primary">{m.score}%</p>
                                                    <p className="text-[8px] uppercase font-black text-zinc-600">{m.status}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* MODULE 2: AFFECTIVE INTELLIGENCE (8 Cols) */}
                    <div className="xl:col-span-8 space-y-8">
                        <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 shadow-sm dark:shadow-2xl">
                            <div className="flex items-center justify-between mb-12">
                                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 flex items-center gap-3">
                                    <HeartPulse size={14} className="text-rose-400" />
                                    Affective Intelligence Logs
                                </h3>
                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <p className="text-[9px] uppercase font-black text-zinc-500">Avg Engagement</p>
                                        <p className="text-xl font-black text-white">{affective.avg_engagement}</p>
                                    </div>
                                    <div className="w-px h-8 bg-white/10" />
                                    <Activity className="text-secondary animate-pulse" />
                                </div>
                            </div>

                            <div className="h-[300px] w-full mb-12">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={affective.engagement_trend}>
                                        <defs>
                                            <linearGradient id="colorEng" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="var(--edu-primary)" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="var(--edu-primary)" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="time" hide />
                                        <YAxis domain={[0, 1]} hide />
                                        <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '12px' }} />
                                        <ReferenceLine y={0.85} stroke="#f43f5e" strokeDasharray="3 3" />
                                        <Area type="monotone" dataKey="score" stroke="var(--edu-primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorEng)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                {affective.emotions.map((e, idx) => (
                                    <div key={idx} className="p-4 bg-white/5 border border-white/5 rounded-3xl text-center">
                                        <p className="text-[9px] uppercase font-black text-zinc-500 mb-1">{e.name}</p>
                                        <p className="text-xl font-black text-white">{e.count}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* MODULE 3: RL POLICY */}
                            <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 shadow-sm dark:shadow-2xl">
                                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 mb-8 flex items-center gap-3">
                                    <Zap size={14} className="text-amber-400" />
                                    RL Policy Distribution
                                </h3>
                                <div className="space-y-6">
                                    {intervention.policy_distribution.map((item, idx) => (
                                        <div key={idx} className="space-y-2">
                                            <div className="flex justify-between items-end text-[10px]">
                                                <span className={`uppercase font-black ${item.name === 'Proactive Intervention' ? 'text-secondary' : 'text-zinc-500'}`}>{item.name}</span>
                                                <span className="font-mono text-zinc-400">{item.value} Hits</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${Math.min(100, (item.value / 20) * 100)}%` }}
                                                    className={`h-full ${item.name === 'Proactive Intervention' ? 'bg-secondary shadow-[0_0_10px_rgba(20,184,166,0.3)]' : 'bg-primary'}`}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* MODULE 4: INTERVENTION AUDIT */}
                            <div className="bg-white dark:bg-zinc-900/10 backdrop-blur-3xl rounded-[40px] border border-edu-border-light dark:border-white/5 p-8 shadow-sm dark:shadow-2xl relative overflow-hidden">
                                <div className="flex items-center justify-between mb-8">
                                    <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 dark:text-slate-400 flex items-center gap-3">
                                        <ShieldCheck size={14} className="text-secondary" />
                                        Intervention Audit
                                    </h3>
                                    <div className="text-right">
                                        <p className="text-2xl font-black text-white leading-none">{intervention.success_rate}%</p>
                                        <p className="text-[8px] text-zinc-500 uppercase font-black uppercase tracking-tighter mt-1">Acceptance Rate</p>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <p className="text-[10px] uppercase font-black text-zinc-600 tracking-[0.2em]">Recent Shadow Swaps</p>
                                    <div className="space-y-2">
                                        {intervention.recent_swaps.map((s, idx) => (
                                            <div key={idx} className="p-3 bg-white/[0.02] border border-white/5 rounded-xl flex items-center justify-between gap-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary border border-secondary/20">
                                                        <Sparkles size={14} />
                                                    </div>
                                                    <div>
                                                        <p className="text-[11px] font-medium text-white">{s.strategy?.replace(/_/g, ' ')}</p>
                                                        <p className="text-[9px] text-zinc-500">{s.timestamp}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-[11px] font-black text-rose-400">Eng: {s.engagement}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Disclaimer */}
                <div className="mt-20 text-center opacity-40 hover:opacity-100 transition-all duration-1000">
                    <p className="text-[10px] text-zinc-400 dark:text-slate-400 uppercase font-bold tracking-[0.4em]">Integrated Cognitive Audit Layer v1.2.0 • alex_123</p>
                </div>

            </div>
        </div>
    );
};

export default DataDashboard;
