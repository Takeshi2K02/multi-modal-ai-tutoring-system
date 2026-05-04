import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import useSWR from 'swr';
import {
    ChevronDown,
    ChevronRight,
    CheckCircle,
    PlayCircle,
    BookOpen,
    Target,
    Award,
    Clock,
    ArrowLeft,
    Loader2,
    Sparkles,
    Zap
} from 'lucide-react';
import { getSynthesis, fetcher, API_BASE_URL, startSessionTopic } from '../services/api';
import SkeletonTopic from '../components/Skeletons/SkeletonTopic';
import { toast } from 'react-hot-toast';

const CurriculumBrowser = ({ 
    sessionId, 
    onBack, 
    onContinue,
    prefetchingTopic,
    setPrefetchingTopic,
    readyTopics,
    setReadyTopics
}) => {
    const { data: sessionData, error, isLoading } = useSWR(
        sessionId ? `${API_BASE_URL}/api/session/${sessionId}` : null,
        fetcher,
        { refreshInterval: 5000 } // Refresh to catch progress updates
    );

    const [expandedLectures, setExpandedLectures] = useState({});
    const [prefetchStatus, setPrefetchStatus] = useState("idle"); // idle | loading | ready | error

    const { session, plan } = sessionData || {};
    const structure = plan?.curriculum?.structure || [];
    const completedTopics = session?.progress?.completed_topics || [];
    const masteryPercent = session?.progress?.percent_complete || 0;

    const nextTopicToLearn = React.useMemo(() => {
        let target = null;
        for (const lecture of structure) {
            for (const topic of (lecture.children || [])) {
                if (!completedTopics.includes(topic.title)) {
                    target = topic.title;
                    break;
                }
            }
            if (target) break;
        }
        return target;
    }, [structure, completedTopics]);

    // Step 4 & 5: Polling & Persistence
    React.useEffect(() => {
        if (!prefetchingTopic || !session?.student_id) return;

        let pollCount = 0;
        const maxPolls = 20;
        const pollInterval = setInterval(async () => {
            try {
                if (import.meta.env.DEV) console.log(`>>> [Prefetch] Polling for manual trigger: ${prefetchingTopic} (${pollCount + 1}/${maxPolls})`);
                const result = await getSynthesis(session.student_id, prefetchingTopic, sessionId);
                
                if (result?.final_content || result?.full_text) {
                    setPrefetchingTopic(null);
                    setReadyTopics(prev => [...new Set([...prev, prefetchingTopic])]);
                    clearInterval(pollInterval);
                }
            } catch (err) {
                console.error(">>> [Prefetch] Polling error:", err);
            }

            pollCount++;
            if (pollCount >= maxPolls) {
                setPrefetchingTopic(null);
                clearInterval(pollInterval);
            }
        }, 5000);

        return () => clearInterval(pollInterval);
    }, [prefetchingTopic, session?.student_id]);

    // Step 5: Persistent Readiness Check on Mount
    React.useEffect(() => {
        if (!structure.length || !session?.student_id) return;

        const checkExisting = async () => {
            const unlockedTopics = [];
            structure.forEach(lecture => {
                (lecture.children || []).forEach(topic => {
                    if (!completedTopics.includes(topic.title)) {
                        unlockedTopics.push(topic.title);
                    }
                });
            });

            for (const title of unlockedTopics) {
                try {
                    const result = await getSynthesis(session.student_id, title, sessionId);
                    if (result?.final_content || result?.full_text) {
                        setReadyTopics(prev => [...new Set([...prev, title])]);
                    }
                } catch (e) {}
            }
        };

        checkExisting();
    }, [structure.length, session?.student_id]);

    // Existing Prefetch Status Polling (Auto-prefetch for next topic)
    React.useEffect(() => {
        if (!nextTopicToLearn || !sessionId || !session?.student_id || prefetchingTopic) return;

        let pollCount = 0;
        const maxPolls = 10; // 50 seconds total at 5s interval
        let pollInterval;

        const checkStatus = async () => {
            try {
                if (import.meta.env.DEV) console.log(`>>> [Prefetch] Polling status for: ${nextTopicToLearn} (${pollCount + 1}/${maxPolls})`);
                const synthesis = await getSynthesis(session.student_id, nextTopicToLearn, sessionId);
                
                if (synthesis && synthesis.status !== "not_ready") {
                    if (import.meta.env.DEV) console.log(">>> [Prefetch] Status: READY");
                    setPrefetchStatus("ready");
                    clearInterval(pollInterval);
                } else {
                    setPrefetchStatus("loading");
                }
            } catch (err) {
                console.error(">>> [Prefetch] Poll failed:", err);
            }

            pollCount++;
            if (pollCount >= maxPolls) {
                if (import.meta.env.DEV) console.log(">>> [Prefetch] Polling timed out");
                clearInterval(pollInterval);
                if (prefetchStatus !== "ready") setPrefetchStatus("idle");
            }
        };

        // Reset and start polling
        setPrefetchStatus("loading");
        checkStatus(); // Initial check
        pollInterval = setInterval(checkStatus, 5000);

        return () => clearInterval(pollInterval);
    }, [nextTopicToLearn, sessionId, session?.student_id]);

    // Fix 2: Start CV pipeline on module page entry
    React.useEffect(() => {
        if (import.meta.env.DEV) console.log(">>> [CV] Module page mounted. Initializing pedagogical sensing...");
        // Activation is handled by the global LiveAffectSensing in App.jsx
    }, []);

    const toggleLecture = (index) => {
        setExpandedLectures(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    if (isLoading) return <div className="p-10"><SkeletonTopic /></div>;
    if (error) return <div className="p-10 text-danger text-center">Failed to load curriculum.</div>;

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark overflow-y-auto custom-scrollbar p-6 lg:p-12 transition-colors">
            <div className="max-w-5xl mx-auto space-y-12">

                {/* Header: Mastery & Goal */}
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div className="space-y-4">
                        <button
                            onClick={onBack}
                            className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 dark:text-slate-500 hover:text-primary transition-colors"
                        >
                            <ArrowLeft size={14} />
                            Dashboard
                        </button>
                        <h1 className="text-4xl lg:text-5xl font-light text-edu-text-light dark:text-white tracking-tight">
                            {plan?.normalized_goal || "Curriculum Overview"}
                        </h1>
                        <p className="text-zinc-500 dark:text-slate-400 font-light flex items-center gap-2">
                            <Target size={16} className="text-primary" />
                            Dynamic path tailored for <span className="font-medium text-primary">{localStorage.getItem('userId') || "User"}</span>
                        </p>
                    </div>

                    <div className="bg-white/60 dark:bg-white/[0.02] backdrop-blur-3xl border border-edu-border-light dark:border-white/5 rounded-[32px] p-6 flex items-center gap-6 shadow-xl transition-all">
                        <div className="relative w-16 h-16">
                            <svg className="w-full h-full -rotate-90">
                                <circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" strokeWidth="4" className="text-zinc-100 dark:text-white/5" />
                                <motion.circle
                                    cx="32"
                                    cy="32"
                                    r="28"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    strokeDasharray="176"
                                    initial={{ strokeDashoffset: 176 }}
                                    animate={{ strokeDashoffset: 176 - (176 * masteryPercent) / 100 }}
                                    className="text-secondary transition-all duration-1000"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center text-xs font-mono font-bold text-secondary">
                                {masteryPercent}%
                            </div>
                        </div>
                        <div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400 dark:text-slate-500 block mb-1">Current Mastery</span>
                            <div className="flex items-center gap-2">
                                <Award size={18} className="text-secondary" />
                                <span className="text-xl font-light text-edu-text-light dark:text-white">Cognitive Progress</span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Curriculum Grid */}
                <div className="space-y-6">
                    {structure.map((lecture, lIdx) => {
                        const isExpanded = expandedLectures[lIdx];
                        const lectureTopics = lecture.children || [];
                        const completedInLecture = lectureTopics.filter(t => completedTopics.includes(t.title)).length;
                        const isLectureComplete = completedInLecture === lectureTopics.length && lectureTopics.length > 0;

                        return (
                            <motion.div
                                key={lIdx}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: lIdx * 0.1 }}
                                className={clsx(
                                    "group bg-white/40 dark:bg-white/[0.01] backdrop-blur-3xl border rounded-[40px] overflow-hidden transition-all duration-500",
                                    isExpanded ? "border-primary/20 dark:border-white/10 ring-1 ring-primary/5 shadow-2xl" : "border-edu-border-light dark:border-white/5 hover:border-primary/20 hover:bg-white/60 dark:hover:bg-white/[0.02]"
                                )}
                            >
                                {/* Lecture Header */}
                                <div
                                    onClick={() => toggleLecture(lIdx)}
                                    className="p-8 flex items-center justify-between cursor-pointer"
                                >
                                    <div className="flex items-center gap-6">
                                        <div className={clsx(
                                            "w-14 h-14 rounded-3xl flex items-center justify-center transition-all duration-500",
                                            isLectureComplete ? "bg-secondary/10 text-secondary" : "bg-primary/5 text-primary group-hover:scale-110"
                                        )}>
                                            {isLectureComplete ? <CheckCircle size={24} /> : <BookOpen size={24} />}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 dark:text-slate-500">Module 0{lIdx + 1}</span>
                                                {isLectureComplete && (
                                                    <span className="px-2 py-0.5 bg-secondary/10 text-secondary text-[8px] font-black uppercase tracking-widest rounded-full">Completed</span>
                                                )}
                                            </div>
                                            <h3 className={clsx(
                                                "text-2xl font-light tracking-tight transition-colors",
                                                isLectureComplete ? "text-secondary/80 line-through" : "text-edu-text-light dark:text-white"
                                            )}>
                                                {lecture.title}
                                            </h3>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-8">
                                        <div className="hidden md:flex flex-col items-end gap-1">
                                            <span className="text-[9px] font-bold text-zinc-400 dark:text-slate-500 uppercase tracking-widest">Efficiency</span>
                                            <div className="flex items-center gap-2">
                                                <Clock size={12} className="text-zinc-300 dark:text-slate-600" />
                                                <span className="text-sm font-mono text-zinc-500 dark:text-slate-400">{lectureTopics.length * 15}m</span>
                                            </div>
                                        </div>
                                        <div className={clsx(
                                            "w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500",
                                            isExpanded ? "bg-primary text-white border-primary rotate-180" : "border-edu-border-light dark:border-white/10 text-zinc-400 group-hover:border-primary/30 group-hover:text-primary"
                                        )}>
                                            <ChevronDown size={18} />
                                        </div>
                                    </div>
                                </div>

                                {/* Lecture Topics (Expandable) */}
                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="border-t border-edu-border-light dark:border-white/5"
                                        >
                                            <div className="p-4 space-y-2 bg-zinc-50/50 dark:bg-black/20">
                                                {lectureTopics.map((topic, tIdx) => {
                                                    const isCompleted = completedTopics.includes(topic.title);
                                                    const isLocked = !isCompleted && topic.title !== nextTopicToLearn;
                                                    const isNext = topic.title === nextTopicToLearn;
                                                    
                                                    return (
                                                        <div
                                                            key={tIdx}
                                                            className={clsx(
                                                                "flex items-center justify-between p-6 bg-white dark:bg-white/[0.01] border border-edu-border-light dark:border-white/5 rounded-[28px] group/topic transition-all",
                                                                isLocked ? "opacity-40 grayscale pointer-events-none" : "hover:border-primary/20 hover:shadow-xl"
                                                            )}
                                                        >
                                                            <div className="flex items-center gap-4">
                                                                <div className={clsx(
                                                                    "w-8 h-8 rounded-xl flex items-center justify-center border transition-colors",
                                                                    isCompleted ? "bg-secondary/10 border-secondary/20 text-secondary" : "border-edu-border-light dark:border-white/10 text-zinc-300 group-hover/topic:border-primary/20 group-hover/topic:text-primary"
                                                                )}>
                                                                    {isCompleted ? <CheckCircle size={16} /> : <div className="w-1.5 h-1.5 rounded-full bg-current" />}
                                                                </div>
                                                                <span className={clsx(
                                                                    "text-base font-light tracking-tight transition-colors",
                                                                    isCompleted ? "text-secondary/60 line-through" : "text-edu-text-light dark:text-slate-200"
                                                                )}>
                                                                    {topic.title}
                                                                </span>
                                                                {topic.title === prefetchingTopic && (
                                                                    <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/10 rounded-full border border-amber-500/20 animate-pulse">
                                                                        <Loader2 size={10} className="text-amber-500 animate-spin" />
                                                                        <span className="text-[9px] font-black uppercase tracking-widest text-amber-500">Synthesizing...</span>
                                                                    </div>
                                                                )}
                                                                {isNext && prefetchStatus === "loading" && topic.title !== prefetchingTopic && (
                                                                    <div className="flex items-center gap-2 px-3 py-1 bg-primary/5 rounded-full border border-primary/10 animate-pulse">
                                                                        <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                                                                        <span className="text-[9px] font-black uppercase tracking-widest text-primary">Preparing lesson...</span>
                                                                    </div>
                                                                )}
                                                                {(readyTopics.includes(topic.title) || (isNext && prefetchStatus === "ready")) && (
                                                                    <div className="flex items-center gap-2 px-3 py-1 bg-secondary/5 rounded-full border border-secondary/10">
                                                                        <Zap size={10} className="text-secondary fill-secondary" />
                                                                        <span className="text-[9px] font-black uppercase tracking-widest text-secondary">Instant Load Ready</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <button
                                                                onClick={() => {
                                                                    if (!isLocked) {
                                                                        onContinue({
                                                                            ...topic,
                                                                            collectionId: plan?.system_metadata?.collection_id
                                                                        });
                                                                    }
                                                                }}
                                                                disabled={isLocked}
                                                                className={clsx(
                                                                    "flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest transition-all",
                                                                    (isLocked || topic.title === prefetchingTopic) ? "bg-zinc-200 dark:bg-white/5 text-zinc-400" : (isCompleted
                                                                        ? "bg-zinc-100 dark:bg-white/5 text-zinc-400 dark:text-slate-500 hover:bg-primary/10 hover:text-primary"
                                                                        : (readyTopics.includes(topic.title) || prefetchStatus === "ready")
                                                                            ? "bg-secondary text-white shadow-lg shadow-secondary/30 ring-2 ring-secondary/20 hover:scale-105 active:scale-95"
                                                                            : "bg-primary text-white shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100")
                                                                )}
                                                            >
                                                                {topic.title === prefetchingTopic ? "Synthesizing..." : (isLocked ? "Locked" : (isCompleted ? "Review Node" : "Continue to Learn"))}
                                                                <PlayCircle size={14} />
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Footer: Knowledge Density */}
                <footer className="pt-12 border-t border-edu-border-light dark:border-white/5 flex flex-col md:flex-row justify-between items-center gap-8 opacity-50">
                    <div className="flex items-center gap-8">
                        <div className="flex flex-col">
                            <span className="text-[8px] font-black uppercase tracking-widest mb-1 text-zinc-400 dark:text-slate-500">Total Nodes</span>
                            <span className="text-xl font-mono text-edu-text-light dark:text-white">{structure.reduce((acc, l) => acc + (l.children?.length || 0), 0)}</span>
                        </div>
                        <div className="w-px h-8 bg-edu-border-light dark:border-white/10" />
                        <div className="flex flex-col">
                            <span className="text-[8px] font-black uppercase tracking-widest mb-1 text-zinc-400 dark:text-slate-500">Synthesized Date</span>
                            <span className="text-sm font-mono text-edu-text-light dark:text-white">{new Date().toLocaleDateString()}</span>
                        </div>
                    </div>
                    <div className="text-[10px] uppercase font-bold tracking-[0.3em] text-primary transition-all animate-pulse">
                        System Optimized for {localStorage.getItem('userId') || "User"}
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default CurriculumBrowser;
