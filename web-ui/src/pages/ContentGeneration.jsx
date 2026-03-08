import React, { useState, useEffect } from 'react';
import { Copy, Check, FileText, ArrowLeft, PlayCircle, Cpu, Code, CheckCircle2, XCircle, BrainCircuit, Sparkles, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE_URL } from '../services/api';

const QuizComponent = ({ quiz, onComplete }) => {
    const [selected, setSelected] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const isCorrect = selected === quiz?.correct_index;

    if (!quiz) return null;

    return (
        <div className="mt-8 p-8 bg-white/50 dark:bg-white/[0.03] backdrop-blur-3xl rounded-[32px] border border-edu-border-light dark:border-white/10 shadow-2xl relative overflow-hidden group transition-colors">
            <div className="absolute top-0 right-0 p-6 opacity-10 dark:opacity-5 text-primary/20 transition-opacity">
                <BrainCircuit size={80} />
            </div>

            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-6 flex items-center gap-2 transition-colors">
                <Sparkles size={14} className="animate-pulse" /> Knowledge Check
            </h4>

            <p className="text-xl font-light text-edu-text-light dark:text-white mb-8 tracking-tight leading-relaxed transition-colors">
                {quiz.question}
            </p>

            <div className="grid grid-cols-1 gap-3">
                {quiz.options.map((option, idx) => (
                    <button
                        key={idx}
                        disabled={isSubmitted}
                        onClick={() => setSelected(idx)}
                        className={`group relative p-4 rounded-2xl border transition-all duration-300 text-left flex items-center justify-between shadow-sm hover:shadow-md ${selected === idx
                            ? 'bg-primary/10 border-primary/50 text-edu-text-light dark:text-white'
                            : 'bg-white/40 dark:bg-white/[0.02] border-edu-border-light dark:border-white/5 text-zinc-500 dark:text-slate-400 hover:border-primary/20 hover:bg-white/60 dark:hover:bg-white/[0.05]'
                            } ${isSubmitted && idx === quiz.correct_index ? 'bg-secondary/10 border-secondary/50 text-secondary' : ''}
                          ${isSubmitted && selected === idx && idx !== quiz.correct_index ? 'bg-danger/10 border-danger/50 text-danger' : ''}`}
                    >
                        <span className="text-sm font-light">{option}</span>
                        {isSubmitted && idx === quiz.correct_index && <CheckCircle2 size={18} className="text-secondary" />}
                        {isSubmitted && selected === idx && idx !== quiz.correct_index && <XCircle size={18} className="text-danger" />}
                    </button>
                ))}
            </div>

            <AnimatePresence>
                {selected !== null && !isSubmitted && (
                    <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        onClick={() => setIsSubmitted(true)}
                        className="mt-8 w-full py-4 bg-primary text-white font-bold rounded-full shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all uppercase tracking-widest text-xs active:scale-95"
                    >
                        Confirm Answer
                    </motion.button>
                )}
            </AnimatePresence>

            {isSubmitted && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-8 p-6 rounded-2xl bg-white/40 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/5 transition-colors"
                >
                    <p className={`text-sm font-medium mb-2 ${isCorrect ? 'text-secondary' : 'text-zinc-600 dark:text-slate-300'}`}>
                        {isCorrect ? '✓ Exceptional reasoning.' : 'Thoughtful attempt.'}
                    </p>
                    <p className="text-xs text-zinc-500 dark:text-slate-500 font-light leading-relaxed transition-colors">
                        {quiz.explanation}
                    </p>
                    <button
                        onClick={onComplete}
                        className="mt-6 text-[10px] font-black text-primary uppercase tracking-widest hover:text-primary/80 transition-colors"
                    >
                        Continue Journey →
                    </button>
                </motion.div>
            )}
        </div>
    );
};

const ContentGeneration = ({ request, sessionId, onBack, onStartLearning }) => {
    const [copied, setCopied] = useState(false);
    const [generatedContent, setGeneratedContent] = useState(null);
    const [isThinking, setIsThinking] = useState(true);
    const [isCompleted, setIsCompleted] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);

    // Dynamic Logic from ToT Directive
    useEffect(() => {
        if (!request?.directive) return;

        const timer = setTimeout(() => {
            setGeneratedContent(request.directive);
            setIsThinking(false);
        }, 1200);

        return () => clearTimeout(timer);
    }, [request]);

    const handleProgressUpdate = async () => {
        if (!sessionId || !request?.topic?.id || isCompleted) return;

        setIsUpdating(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/session/progress`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    topic_id: request.topic.id
                })
            });

            if (res.ok) {
                setIsCompleted(true);
            }
        } catch (err) {
            console.error("Progress Sync Empty:", err);
        } finally {
            setIsUpdating(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(JSON.stringify(request, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!request) return <div className="p-10 text-slate-500">No Generation Request Found.</div>;

    return (
        <div className="flex flex-col lg:flex-row h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark text-edu-text-light dark:text-slate-100 transition-colors p-0 font-sans">

            {/* Nav Padding Offset Container */}
            <div className="flex-1 flex flex-col pt-28 h-full overflow-hidden relative">

                {/* Background Aesthetics */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full" />
                    <div className="absolute bottom-1/4 right-1/4 w-[30%] h-[30%] bg-secondary/5 blur-[100px] rounded-full" />
                </div>

                <div className="flex flex-1 h-full overflow-hidden p-6 gap-6 relative z-10">

                    {/* LEFT COLUMN: ToT Context */}
                    <div className="hidden lg:flex w-80 flex-col gap-6">
                        <div className="bg-white/50 dark:bg-zinc-900/10 border border-edu-border-light dark:border-white/5 rounded-[32px] p-6 backdrop-blur-3xl shadow-sm dark:shadow-2xl transition-all">
                            <h2 className="text-[9px] font-black uppercase tracking-[0.3em] text-primary mb-6 transition-colors">Agentic Context</h2>
                            <div className="space-y-4">
                                <div>
                                    <span className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-bold block mb-1">Strategy</span>
                                    <p className="text-sm font-light text-zinc-600 dark:text-slate-300 transition-colors">{request.selectedStrategy?.pathTitle || 'Adaptive'}</p>
                                </div>
                                <div>
                                    <span className="text-[10px] text-zinc-400 dark:text-slate-500 uppercase font-bold block mb-1">Target Persona</span>
                                    <p className="text-sm font-light text-primary transition-colors">{request.studentPersona?.name}</p>
                                </div>
                                <div className="flex flex-wrap gap-1.5 pt-2">
                                    {request.selectedStrategy?.techniques?.map(t => (
                                        <span key={t} className="px-2 py-0.5 rounded-full bg-primary/10 text-[9px] text-primary border border-primary/20 transition-colors">
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* JSON Inspector */}
                        <div className="flex-1 bg-white/40 dark:bg-white/[0.01] border border-edu-border-light dark:border-white/5 rounded-[32px] overflow-hidden flex flex-col transition-colors">
                            <div className="bg-white/60 dark:bg-white/[0.03] p-4 flex items-center justify-between border-b border-edu-border-light dark:border-white/5 transition-colors">
                                <span className="text-[9px] font-mono text-zinc-400 dark:text-slate-500 uppercase tracking-widest">ToT_Directive.json</span>
                                <button onClick={handleCopy} className="text-zinc-400 hover:text-primary dark:text-slate-500 dark:hover:text-white transition-colors">
                                    {copied ? <Check size={12} className="text-secondary" /> : <Copy size={12} />}
                                </button>
                            </div>
                            <div className="p-4 overflow-auto flex-1 custom-scrollbar">
                                <pre className="text-[9px] font-mono text-secondary dark:text-emerald-400/60 leading-relaxed whitespace-pre-wrap transition-colors">
                                    {JSON.stringify(request.directive, null, 2)}
                                </pre>
                            </div>
                        </div>
                    </div>

                    {/* MAIN CONTENT AREA */}
                    <div className="flex-1 flex flex-col bg-white/60 dark:bg-white/[0.02] border border-edu-border-light dark:border-white/10 rounded-[40px] shadow-sm dark:shadow-2xl overflow-hidden backdrop-blur-2xl relative transition-all">

                        {/* Renderer Header */}
                        <div className="px-8 py-6 border-b border-edu-border-light dark:border-white/5 flex items-center justify-between bg-zinc-100/50 dark:bg-black/20 transition-colors">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-2xl bg-primary/10 dark:bg-indigo-600/20 flex items-center justify-center border border-primary/20 dark:border-indigo-500/30 transition-colors">
                                    <FileText size={20} className="text-primary" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-light text-edu-text-light dark:text-white tracking-tight leading-none mb-1 transition-colors">{request.topic?.title}</h3>
                                    <span className="text-[9px] font-black uppercase tracking-widest text-secondary/70 transition-colors">
                                        Synthesized Content • {generatedContent?.type || 'Thinking...'}
                                    </span>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button onClick={onBack} className="px-5 py-2.5 rounded-full text-zinc-500 dark:text-slate-400 hover:text-primary dark:hover:text-white hover:bg-white dark:hover:bg-white/5 text-xs font-bold uppercase tracking-widest transition-all">
                                    <ArrowLeft size={14} className="inline mr-2" /> Back
                                </button>
                            </div>
                        </div>

                        {/* Dynamic Render Body */}
                        <div className="flex-1 overflow-y-auto p-8 lg:p-12 custom-scrollbar">
                            <div className="max-w-3xl mx-auto">
                                {isThinking ? (
                                    <div className="h-64 flex flex-col items-center justify-center gap-4">
                                        <div className="w-12 h-12 border-2 border-primary/20 border-t-primary rounded-full animate-spin transition-colors" />
                                        <div className="text-[10px] font-black uppercase tracking-[0.4em] text-primary animate-pulse transition-colors">
                                            Generating Intelligent Path...
                                        </div>
                                    </div>
                                ) : (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.8 }}
                                        className="space-y-12"
                                    >
                                        {/* Content Block */}
                                        <div className="prose prose-invert prose-indigo max-w-none">
                                            <div className="text-edu-text-light/90 dark:text-slate-300 font-light text-lg leading-relaxed whitespace-pre-wrap font-serif transition-colors">
                                                {generatedContent?.content}
                                            </div>
                                        </div>

                                        {/* Conditional MCQ Component */}
                                        {generatedContent?.type === 'quiz' && (
                                            <QuizComponent
                                                quiz={generatedContent.quiz}
                                                onComplete={handleProgressUpdate}
                                            />
                                        )}

                                        {/* Completion UI */}
                                        <div className="pt-12 border-t border-edu-border-light dark:border-white/5 flex flex-col items-center gap-6 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-zinc-100 dark:bg-white/5 flex items-center justify-center text-zinc-400 dark:text-slate-500 transition-colors">
                                                    <Database size={14} />
                                                </div>
                                                <span className="text-[10px] font-bold text-zinc-500 dark:text-slate-600 uppercase tracking-[0.2em] transition-colors">Learning Session Persisted</span>
                                            </div>

                                            {!isCompleted ? (
                                                <button
                                                    onClick={handleProgressUpdate}
                                                    disabled={isUpdating}
                                                    className="group relative px-12 py-5 bg-primary text-white font-black rounded-full overflow-hidden transition-all hover:scale-105 active:scale-95 disabled:opacity-50 shadow-xl shadow-primary/20"
                                                >
                                                    <div className="absolute inset-0 bg-gradient-to-r from-primary to-secondary opacity-0 group-hover:opacity-20 transition-opacity" />
                                                    <span className="relative flex items-center gap-3 uppercase tracking-widest text-xs">
                                                        {isUpdating ? 'Synchronizing...' : 'Mark Module Complete'}
                                                        <CheckCircle2 size={16} />
                                                    </span>
                                                </button>
                                            ) : (
                                                <motion.div
                                                    initial={{ scale: 0.9, opacity: 0 }}
                                                    animate={{ scale: 1, opacity: 1 }}
                                                    className="px-10 py-4 bg-secondary/10 border border-secondary/20 rounded-full flex items-center gap-3 text-secondary transition-colors"
                                                >
                                                    <CheckCircle2 size={20} />
                                                    <span className="text-xs font-black uppercase tracking-widest">Mastery Level Updated</span>
                                                </motion.div>
                                            )}

                                            <button
                                                onClick={onStartLearning}
                                                className="mt-4 text-xs font-bold text-zinc-400 hover:text-primary dark:text-slate-500 dark:hover:text-primary transition-colors uppercase tracking-[0.3em]"
                                            >
                                                Next Topic Concept
                                            </button>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default ContentGeneration;
