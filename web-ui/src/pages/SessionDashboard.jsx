import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { getStudentSessions, deleteSession } from '../services/api';
import { Trash2, BookOpen, Clock, ArrowRight, Layers, AlertCircle } from 'lucide-react';

const SessionDashboard = ({ onBack, onResume }) => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState(null);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = () => {
        getStudentSessions("student_001")
            .then(data => {
                if (data && data.sessions) {
                    setSessions(data.sessions);
                }
            })
            .catch(err => console.error("Failed to load dashboard:", err))
            .finally(() => setLoading(false));
    };

    const handleDeleteClick = (id) => {
        setDeletingId(id);
    };

    const confirmDelete = async () => {
        if (!deletingId) return;

        try {
            await deleteSession(deletingId);
            setSessions(prev => prev.filter(s => s._id !== deletingId));
            setDeletingId(null);
        } catch (err) {
            console.error("Failed to delete session", err);
            alert("Failed to delete the session. Please try again.");
        }
    };

    return (
        <div className="h-full w-full overflow-y-auto p-4 md:p-8 font-sans scroll-smooth">
            {/* Delete Confirmation Modal */}
            <AnimatePresence>
                {deletingId && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-slate-900 rounded-2xl shadow-2xl p-6 max-w-sm w-full border border-slate-700 ring-1 ring-white/10"
                        >
                            <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
                                <Trash2 className="text-red-500" size={24} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Delete Session?</h3>
                            <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                                Are you sure you want to remove this learning session? This action cannot be undone.
                            </p>
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setDeletingId(null)}
                                    className="px-4 py-2 text-slate-300 font-bold text-sm hover:bg-slate-800 rounded-lg transition-colors border border-transparent hover:border-slate-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmDelete}
                                    className="px-4 py-2 text-white font-bold text-sm bg-red-600 hover:bg-red-500 rounded-lg transition-colors shadow-lg shadow-red-900/20"
                                >
                                    Delete Forever
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            <div className="max-w-7xl mx-auto pb-20">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight mb-2">My Learning Dashboard</h1>
                        <p className="text-slate-400 flex items-center gap-2">
                            <Layers size={16} /> Track your progress and resume active paths
                        </p>
                    </div>
                </div>

                {loading ? (
                    <div className="text-center py-20">
                        <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
                        <p className="text-slate-500 text-sm font-mono">Loading history...</p>
                    </div>
                ) : (
                    <>
                        {sessions.length === 0 ? (
                            <div className="bg-slate-900/50 rounded-2xl p-16 text-center border border-slate-800/50 shadow-sm border-dashed">
                                <span className="text-6xl mb-6 block grayscale opacity-30">📚</span>
                                <h3 className="text-2xl font-bold text-slate-200 mb-3">No Active Sessions</h3>
                                <p className="text-slate-500 mb-8 max-w-md mx-auto">
                                    You haven't started any structured learning sessions yet. Use the Plan tool to create your first curriculum.
                                </p>
                                <button onClick={onBack} className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-indigo-900/30 hover:bg-indigo-500 hover:scale-105 transition-all">
                                    Create New Plan
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {sessions.map((session, idx) => (
                                    <motion.div
                                        key={session._id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 hover:bg-slate-800/60 hover:border-slate-600 transition-all group flex flex-col relative overflow-hidden backdrop-blur-sm"
                                    >
                                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 opacity-50" />

                                        <div className="flex-1">
                                            <div className="flex justify-between items-start mb-4">
                                                <span className={clsx("px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
                                                    session.status === "COMPLETED" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                                                        session.status === "IN_PROGRESS" ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" :
                                                            "bg-slate-700/30 text-slate-400 border-slate-600"
                                                )}>
                                                    {session.status.replace("_", " ")}
                                                </span>

                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                                                        <Clock size={10} />
                                                        {new Date(session.last_accessed_at).toLocaleDateString()}
                                                    </span>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDeleteClick(session._id);
                                                        }}
                                                        className="text-slate-600 hover:text-red-400 transition-colors p-1.5 hover:bg-slate-700/50 rounded"
                                                        title="Delete Session"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </div>

                                            <h3 className="text-lg font-bold text-slate-100 line-clamp-2 mb-3 leading-snug group-hover:text-indigo-300 transition-colors" title={session.goal_title}>
                                                {session.goal_title}
                                            </h3>

                                            <div className="flex items-center gap-2 text-xs text-slate-500 mb-6">
                                                <BookOpen size={14} />
                                                <span>{session.goal_topics_count} Topics</span>
                                            </div>
                                        </div>

                                        <div className="mt-auto">
                                            <div className="flex justify-between text-[10px] text-slate-400 mb-2 uppercase tracking-wider font-bold">
                                                <span>Progress</span>
                                                <span className="text-white">{session.progress.percent_complete}%</span>
                                            </div>
                                            <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden mb-5">
                                                <div
                                                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-1000"
                                                    style={{ width: `${session.progress.percent_complete}%` }}
                                                />
                                            </div>
                                            <button
                                                onClick={() => onResume(session._id)}
                                                className="w-full py-3 bg-indigo-600/10 border border-indigo-500/20 text-indigo-300 font-bold rounded-xl hover:bg-indigo-600 hover:text-white transition-all text-xs flex items-center justify-center gap-2 group-hover:shadow-lg group-hover:shadow-indigo-900/20"
                                            >
                                                <span>Resume Session</span>
                                                <ArrowRight size={14} />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default SessionDashboard;
