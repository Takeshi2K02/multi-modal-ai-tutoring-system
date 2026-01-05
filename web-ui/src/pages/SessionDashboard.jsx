import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { getStudentSessions, deleteSession } from '../services/api'; // Import deleteSession
import { Trash2 } from 'lucide-react'; // Import Icon

const SessionDashboard = ({ onBack, onResume }) => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState(null); // ID of session to be deleted

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
            // Optimistic update or reload? Reload to be safe.
            setSessions(prev => prev.filter(s => s._id !== deletingId));
            setDeletingId(null);
        } catch (err) {
            console.error("Failed to delete session", err);
            alert("Failed to delete the session. Please try again.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 font-sans p-8 relative">
            {/* Delete Confirmation Modal */}
            <AnimatePresence>
                {deletingId && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-white rounded-xl shadow-2xl p-6 max-w-sm w-full border border-slate-200"
                        >
                            <h3 className="text-lg font-bold text-slate-800 mb-2">Delete Session?</h3>
                            <p className="text-slate-500 text-sm mb-6">
                                Are you sure you want to remove this learning session? This action cannot be undone.
                            </p>
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setDeletingId(null)}
                                    className="px-4 py-2 text-slate-600 font-bold text-sm bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmDelete}
                                    className="px-4 py-2 text-white font-bold text-sm bg-red-500 hover:bg-red-600 rounded-lg transition-colors"
                                >
                                    Delete
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">My Learning Dashboard</h1>
                        <p className="text-slate-500 mt-2">Track progress and resume active learning paths</p>
                    </div>
                    <button
                        onClick={onBack}
                        className="px-6 py-2 bg-white border border-slate-200 text-slate-600 font-bold rounded-lg shadow-sm hover:bg-slate-50 transition-all"
                    >
                        &larr; Back to Tools
                    </button>
                </div>

                {loading ? (
                    <div className="text-center py-20 text-slate-400">Loading your history...</div>
                ) : (
                    <>
                        {sessions.length === 0 ? (
                            <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm">
                                <span className="text-6xl mb-4 block opacity-20">📚</span>
                                <h3 className="text-xl font-bold text-slate-700 mb-2">No Active Sessions</h3>
                                <p className="text-slate-500 mb-8">You haven't started any structured learning sessions yet.</p>
                                <button onClick={onBack} className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all">
                                    Start New Goal
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {sessions.map((session, idx) => (
                                    <motion.div
                                        key={session._id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow flex flex-col h-64 group relative"
                                    >
                                        <div className="flex-1">
                                            <div className="flex justify-between items-start mb-4">
                                                <span className={clsx("px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider",
                                                    session.status === "COMPLETED" ? "bg-emerald-100 text-emerald-700" :
                                                        session.status === "IN_PROGRESS" ? "bg-indigo-100 text-indigo-700" :
                                                            "bg-slate-100 text-slate-600"
                                                )}>
                                                    {session.status.replace("_", " ")}
                                                </span>

                                                {/* Delete Button - Visible on Hover or Always? Always is discoverable. */}
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs text-slate-400 font-mono">
                                                        {new Date(session.last_accessed_at).toLocaleDateString()}
                                                    </span>
                                                    <button
                                                        onClick={() => handleDeleteClick(session._id)}
                                                        className="text-slate-300 hover:text-red-500 transition-colors p-1"
                                                        title="Delete Session"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                            <h3 className="text-lg font-bold text-slate-800 line-clamp-2 mb-2" title={session.goal_title}>
                                                {session.goal_title}
                                            </h3>
                                            <p className="text-sm text-slate-500">
                                                {session.goal_topics_count} Topics Identified
                                            </p>
                                        </div>

                                        <div className="mt-6">
                                            <div className="flex justify-between text-xs text-slate-500 mb-1">
                                                <span>Progress</span>
                                                <span className="font-bold text-slate-700">{session.progress.percent_complete}%</span>
                                            </div>
                                            <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
                                                <div
                                                    className="h-full bg-emerald-500 rounded-full transition-all duration-1000"
                                                    style={{ width: `${session.progress.percent_complete}%` }}
                                                />
                                            </div>
                                            <button
                                                onClick={() => onResume(session._id)}
                                                className="w-full py-2 bg-indigo-50 text-indigo-600 font-bold rounded-lg hover:bg-indigo-100 transition-colors text-sm"
                                            >
                                                Resume Session &rarr;
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
