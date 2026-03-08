import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import useSWR from 'swr';
import { getStudentSessions, deleteSession, fetcher, API_BASE_URL } from '../services/api';
import { Trash2, BookOpen, Clock, ArrowRight, Layers, Sparkles } from 'lucide-react';
import SkeletonCard from '../components/Skeletons/SkeletonCard';

/**
 * SessionDashboard Component (My Learning)
 * 
 * DESIGN RATIONALE:
 * 1. Zen-mode Layout: Maximizes negative space and uses large, light typography for focus.
 * 2. Glassmorphism Architecture: Cards use deep backdrop blur and paper-thin borders to feel like floating glass.
 * 3. High-Contrast Progress: Uses vibrant gradients (Indigo -> Purple) against a deep black canvas.
 */
const SessionDashboard = ({ onBack, onResume }) => {
    const { data, error, isLoading, mutate } = useSWR(`${API_BASE_URL}/api/sessions/student/student_001`, fetcher);
    const sessions = data?.sessions || [];
    const [deletingId, setDeletingId] = useState(null);

    const handleDeleteClick = (id) => {
        setDeletingId(id);
    };

    const confirmDelete = async () => {
        if (!deletingId) return;

        try {
            await deleteSession(deletingId);
            // Optimistically update the UI
            mutate({ ...data, sessions: sessions.filter(s => s._id !== deletingId) }, false);
            setDeletingId(null);
        } catch (err) {
            console.error("Failed to delete session", err);
            // Revalidate on error
            mutate();
        }
    };

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark font-sans selection:bg-primary/30 overflow-y-auto transition-colors">

            {/* Delete Confirmation Modal (Glassmorphism) - z-[110] covers Navbar */}
            <AnimatePresence>
                {deletingId && (
                    <div className="fixed inset-0 z-[110] flex items-center justify-center p-6 bg-black/40 dark:bg-black/60 backdrop-blur-md transition-colors">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="bg-white dark:bg-zinc-900/80 backdrop-blur-3xl rounded-[32px] border border-edu-border-light dark:border-white/5 p-8 max-w-md w-full shadow-2xl transition-colors"
                        >
                            <div className="w-14 h-14 bg-danger/10 rounded-full flex items-center justify-center mb-6 border border-danger/20">
                                <Trash2 className="text-danger" size={24} strokeWidth={1.5} />
                            </div>
                            <h3 className="text-2xl font-light text-edu-text-light dark:text-white mb-3 transition-colors">Terminate Session?</h3>
                            <p className="text-zinc-500 dark:text-zinc-400 text-[15px] mb-8 leading-relaxed font-light transition-colors">
                                This will permanently remove your learning progress and vector mappings for this path.
                            </p>
                            <div className="flex gap-4">
                                <button
                                    onClick={() => setDeletingId(null)}
                                    className="flex-1 py-4 bg-zinc-100 dark:bg-zinc-800/50 hover:bg-zinc-200 dark:hover:bg-zinc-800 text-zinc-500 dark:text-zinc-400 font-bold rounded-2xl transition-all border border-edu-border-light dark:border-white/5"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmDelete}
                                    className="flex-1 py-4 bg-danger hover:opacity-90 text-white font-bold rounded-2xl transition-all shadow-lg shadow-danger/20"
                                >
                                    Delete Path
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">

                {/* Header Section (Zen-mode) */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="mb-20"
                >
                    <h1 className="text-5xl md:text-6xl font-light tracking-tight text-edu-text-light dark:text-white mb-6">
                        My <br />
                        <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-400 to-primary animate-gradient-x shadow-sm">
                            Knowledge Paths
                        </span>
                    </h1>
                    <div className="flex items-center gap-4 text-zinc-400 dark:text-zinc-500 text-lg font-light transition-colors">
                        <Layers size={18} strokeWidth={1.5} />
                        <span>Tracking {sessions.length} active learning trajectories</span>
                    </div>
                </motion.div>

                {isLoading && sessions.length === 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
                    </div>
                ) : (
                    <AnimatePresence mode="popLayout">
                        {sessions.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="bg-white/50 dark:bg-zinc-900/30 backdrop-blur-2xl rounded-[48px] border border-edu-border-light dark:border-white/5 p-20 text-center shadow-sm transition-colors"
                            >
                                <div className="w-20 h-20 bg-zinc-50 dark:bg-zinc-950 border border-edu-border-light dark:border-white/5 rounded-full flex items-center justify-center mx-auto mb-8 shadow-inner text-4xl transition-colors">
                                    🔕
                                </div>
                                <h3 className="text-3xl font-light text-edu-text-light dark:text-zinc-200 mb-4 tracking-tight transition-colors">Silent Trajectories</h3>
                                <p className="text-zinc-500 dark:text-zinc-500 mb-12 max-w-sm mx-auto font-light leading-relaxed transition-colors">
                                    No active learning paths detected. Begin a new synthesis to start tracked session.
                                </p>
                                <button
                                    onClick={onBack}
                                    className="inline-flex items-center gap-3 px-10 py-5 bg-primary text-white font-bold rounded-full hover:bg-primary/90 hover:scale-105 transition-all shadow-xl shadow-primary/20 group"
                                >
                                    <span>Plan New Synthesis</span>
                                    <Sparkles size={18} className="text-white group-hover:scale-125 transition-transform" />
                                </button>
                            </motion.div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {sessions.map((session, idx) => (
                                    <motion.div
                                        key={session._id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05, duration: 0.5 }}
                                        className="group relative bg-zinc-900/40 backdrop-blur-3xl rounded-[32px] border border-white/5 p-8 hover:bg-zinc-900/60 hover:border-white/10 transition-all duration-500 flex flex-col overflow-hidden"
                                    >
                                        {/* Status Header */}
                                        <div className="flex justify-between items-center mb-8 relative z-10">
                                            <div className={clsx(
                                                "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-[0.2em] border shadow-sm transition-colors",
                                                session.status === "COMPLETED" ? "bg-secondary/10 text-secondary border-secondary/20" :
                                                    session.status === "IN_PROGRESS" ? "bg-primary/10 text-primary border-primary/20" :
                                                        "bg-zinc-100 dark:bg-zinc-800/50 text-zinc-400 dark:text-zinc-500 border-edu-border-light dark:border-zinc-700/30"
                                            )}>
                                                {session.status.replace("_", " ")}
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <span className="text-[10px] text-zinc-400 dark:text-zinc-600 font-mono flex items-center gap-2 transition-colors">
                                                    <Clock size={12} strokeWidth={1.5} />
                                                    {new Date(session.last_accessed_at).toLocaleDateString()}
                                                </span>
                                                <button
                                                    onClick={() => handleDeleteClick(session._id)}
                                                    className="p-2 text-zinc-300 dark:text-zinc-700 hover:text-danger transition-colors bg-white/50 dark:bg-zinc-950/50 rounded-lg border border-edu-border-light dark:border-white/5 opacity-0 group-hover:opacity-100 duration-300"
                                                >
                                                    <Trash2 size={14} strokeWidth={1.5} />
                                                </button>
                                            </div>
                                        </div>

                                        {/* Content Section */}
                                        <div className="flex-1 mb-10 relative z-10">
                                            <h3 className="text-2xl font-light text-edu-text-light dark:text-zinc-100 group-hover:text-primary dark:group-hover:text-white transition-colors leading-tight mb-4 tracking-tight line-clamp-2">
                                                {session.goal_title}
                                            </h3>
                                            <div className="flex items-center gap-3 text-zinc-400 dark:text-zinc-500 font-light text-sm transition-colors">
                                                <BookOpen size={14} strokeWidth={1.5} className="text-primary" />
                                                <span>{session.goal_topics_count} Specialized Topics</span>
                                            </div>
                                        </div>

                                        {/* Progress & Action */}
                                        <div className="mt-auto space-y-8 relative z-10">
                                            <div className="space-y-3">
                                                <div className="flex justify-between items-end">
                                                    <span className="text-[10px] text-zinc-400 dark:text-zinc-600 font-bold uppercase tracking-widest transition-colors">Mastery Level</span>
                                                    <span className="text-lg font-light text-edu-text-light dark:text-white tracking-tighter transition-colors">{session.progress.percent_complete}%</span>
                                                </div>
                                                <div className="h-1.5 bg-zinc-100 dark:bg-zinc-950 rounded-full overflow-hidden border border-edu-border-light dark:border-white/5 transition-colors">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${session.progress.percent_complete}%` }}
                                                        transition={{ duration: 1.5, ease: "easeOut" }}
                                                        className="h-full bg-gradient-to-r from-primary via-accent to-secondary"
                                                    />
                                                </div>
                                            </div>

                                            <button
                                                onClick={() => onResume(session._id)}
                                                className="w-full py-4 bg-primary text-white font-bold rounded-2xl flex items-center justify-center gap-3 hover:bg-primary/90 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-xl shadow-primary/20"
                                            >
                                                <span>Resume Synthesis</span>
                                                <ArrowRight size={16} strokeWidth={2.5} className="group-hover:translate-x-1 transition-transform" />
                                            </button>
                                        </div>

                                        {/* Hover Underglow */}
                                        <div className="absolute inset-0 rounded-[32px] border border-white/5 pointer-events-none opacity-20 group-hover:opacity-40 transition-opacity animate-pulse" />
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </AnimatePresence>
                )}

                {/* Footer Section */}
                <div className="mt-32 pt-12 border-t border-edu-border-light dark:border-white/[0.03] text-center transition-colors">
                    <p className="text-[10px] text-zinc-400 dark:text-zinc-800 uppercase tracking-[0.5em] leading-loose">
                        EduSynth Cognitive Dashboard <br />
                        <span className="text-zinc-500 dark:text-zinc-900">Research Build 2.4.0 (Multimodal Core)</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SessionDashboard;
