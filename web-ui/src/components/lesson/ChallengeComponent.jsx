import React, { useState } from 'react';
import { BrainCircuit, Gamepad2 } from 'lucide-react';
import { useAuth } from "../../AuthContext";
import { evaluateChallenge } from "../../services/api";
import { CheckCircle2, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

const ChallengeComponent = ({ topic, context, onComplete, sessionId }) => {
    const { userId } = useAuth();
    const [response, setResponse] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [score, setScore] = useState(null);

    const handleSubmit = async () => {
        if (!response.trim() || isEvaluating) return;
        setIsEvaluating(true);
        try {
            const result = await evaluateChallenge({
                student_id: userId,
                session_id: sessionId,
                topic_id: topic,
                response: response,
                context: context
            });
            setFeedback(result.feedback);
            setScore(result.score);
            if (result.score >= 0.7) {
                onComplete(response, result.score);
            }
        } catch (err) {
            console.error("Challenge Error:", err);
        } finally {
            setIsEvaluating(false);
        }
    };

    return (
        <div className="mt-12 p-8 bg-[#121212] rounded-[40px] border border-white/5 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-5 text-primary">
                <BrainCircuit size={100} />
            </div>

            <div className="relative z-10 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                        <Gamepad2 size={20} className="text-primary" />
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Active Design Challenge</h4>
                        <p className="text-sm text-zinc-400 font-light">Apply your knowledge to solve this problem</p>
                    </div>
                </div>

                <div className="space-y-4">
                    <textarea
                        value={response}
                        onChange={(e) => setResponse(e.target.value)}
                        placeholder="Define 3-5 core attributes for this design..."
                        disabled={score >= 0.7}
                        className="w-full min-h-[160px] bg-black/40 border border-white/10 rounded-3xl p-6 text-zinc-300 placeholder:text-zinc-700 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all resize-none font-mono text-sm leading-relaxed"
                    />

                    {!feedback && (
                        <button
                            onClick={handleSubmit}
                            disabled={!response.trim() || isEvaluating}
                            className="w-full py-5 bg-primary text-white font-black rounded-full shadow-xl shadow-primary/10 hover:scale-[1.02] active:scale-95 disabled:opacity-30 disabled:grayscale transition-all flex items-center justify-center gap-3 uppercase tracking-[0.2em] text-xs"
                        >
                            {isEvaluating ? 'AI Processing...' : 'Submit for Evaluation'}
                        </button>
                    )}
                </div>

                <AnimatePresence>
                    {feedback && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={clsx(
                                "p-6 rounded-3xl border backdrop-blur-md",
                                score >= 0.7 ? "bg-secondary/5 border-secondary/20" : "bg-danger/5 border-danger/20"
                            )}
                        >
                            <div className="flex items-start gap-4">
                                <div className={clsx(
                                    "w-8 h-8 rounded-xl flex items-center justify-center shrink-0",
                                    score >= 0.7 ? "bg-secondary/20 text-secondary" : "bg-danger/20 text-danger"
                                )}>
                                    {score >= 0.7 ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                                </div>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-3">
                                        <span className="text-xs font-black uppercase tracking-widest text-zinc-400">AI Feedback</span>
                                        <span className={clsx(
                                            "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full",
                                            score >= 0.7 ? "bg-secondary/10 text-secondary" : "bg-danger/10 text-danger"
                                        )}>
                                            Score: {(score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-sm font-light leading-relaxed text-zinc-300">{feedback}</p>
                                    {score < 0.7 && (
                                        <button
                                            onClick={() => { setFeedback(null); setScore(null); }}
                                            className="text-[10px] font-black uppercase tracking-widest text-primary hover:opacity-80 transition-opacity"
                                        >
                                            Try Again →
                                        </button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default ChallengeComponent;
