import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx'; // Added clsx import
import {
    BrainCircuit,
    Sparkles,
    CheckCircle2,
    XCircle,
    ArrowLeft,
    Gamepad2,
    FileText,
    Database,
    ChevronRight,
    Send,
    AlertCircle
} from 'lucide-react';
import DynamicVisualContainer from '../components/DynamicVisualContainer';
import Mermaid from '../components/Mermaid';
import {
    runSimulation,
    savePerformance,
    updateSessionProgress,
    evaluateChallenge,
    saveLessonContent,
    getLessonContent,
    syncStudentProgress,
    handleUserFeedback
} from '../services/api';

const ChallengeComponent = ({ topic, context, onComplete, sessionId }) => {
    const [response, setResponse] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [score, setScore] = useState(null);

    const handleSubmit = async () => {
        if (!response.trim() || isEvaluating) return;
        setIsEvaluating(true);
        try {
            const result = await evaluateChallenge({
                student_id: "student_001",
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
                            <Send size={16} />
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

// --- Guardrails & Error Boundary ---
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) { return { hasError: true }; }
    componentDidCatch(error, errorInfo) { console.error(">>> Component Crash Handled:", error, errorInfo); }
    render() {
        if (this.state.hasError) {
            return (
                <div className="p-8 rounded-3xl border border-danger/20 bg-danger/5 text-center">
                    <p className="text-sm text-danger font-medium">Interactive component failed to load.</p>
                </div>
            );
        }
        return this.props.children;
    }
}

const QuizComponent = ({ quiz, onOptionSelect, isSubmitted, selectedOption, correctIndex }) => {
    // Robust Null-Checks for AI-generated data
    if (!quiz || !quiz.questions || !Array.isArray(quiz.questions)) {
        return (
            <div className="mt-8 p-6 bg-white/5 dark:bg-white/[0.02] rounded-3xl border border-white/5 flex items-center gap-3">
                <AlertCircle className="text-zinc-500" size={16} />
                <span className="text-xs text-zinc-500 italic">Quiz structure initialization failed. Skipping...</span>
            </div>
        );
    }

    return (
        <div className="mt-12 p-10 bg-[#121212] rounded-[48px] border border-white/5 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-5 text-primary">
                <Sparkles size={120} />
            </div>

            <div className="relative z-10">
                <div className="flex items-center gap-4 mb-8">
                    <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                        <BrainCircuit size={20} className="text-primary" />
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Knowledge Synthesis Check</h4>
                        <p className="text-xs text-zinc-500 font-light">Validate your understanding of the core concepts</p>
                    </div>
                </div>

                {quiz.questions.map((q, qIdx) => (
                    <div key={qIdx} className="space-y-8">
                        <p className="text-2xl font-light text-white tracking-tight leading-relaxed">
                            {q.question}
                        </p>

                        <div className="grid grid-cols-1 gap-4">
                            {q.options?.map((option, idx) => {
                                const isSelected = selectedOption === idx;
                                const isCorrect = idx === q.correct_index;

                                let btnClass = "bg-white/[0.02] border-white/5 text-zinc-400 hover:border-primary/30 hover:bg-white/[0.04]";
                                if (isSelected) btnClass = "bg-primary/10 border-primary/50 text-white shadow-lg shadow-primary/10";
                                if (isSubmitted) {
                                    if (isCorrect) btnClass = "bg-secondary/10 border-secondary/50 text-secondary shadow-lg shadow-secondary/10";
                                    else if (isSelected) btnClass = "bg-danger/10 border-danger/50 text-danger shadow-lg shadow-danger/10";
                                }

                                return (
                                    <button
                                        key={idx}
                                        disabled={isSubmitted}
                                        onClick={() => onOptionSelect(idx)}
                                        className={`p-6 rounded-3xl border transition-all duration-300 text-left flex items-center justify-between text-base ${btnClass}`}
                                    >
                                        <span className="font-light">{option}</span>
                                        {isSubmitted && isCorrect && <CheckCircle2 size={20} className="text-secondary" />}
                                        {isSubmitted && isSelected && !isCorrect && <XCircle size={20} className="text-danger" />}
                                    </button>
                                );
                            })}
                        </div>

                        {isSubmitted && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-6 rounded-3xl bg-white/[0.02] border border-white/5"
                            >
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center shrink-0">
                                        <FileText size={16} className="text-zinc-400" />
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-xs font-black uppercase tracking-widest text-zinc-500">Pedagogical Insight</p>
                                        <p className="text-sm font-light leading-relaxed text-zinc-400">{q.explanation}</p>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

const LessonView = ({ sessionId, topic, onBack, onReady }) => {
    const [loading, setLoading] = useState(true);
    const [content, setContent] = useState(null);
    const [isThinking, setIsThinking] = useState(true);
    const [selectedOption, setSelectedOption] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isChallengeComplete, setIsChallengeComplete] = useState(false);
    const [isCompleting, setIsCompleting] = useState(false);
    const [response, setResponse] = useState('');
    const [error, setError] = useState(null);
    const [isVisualReady, setIsVisualReady] = useState(false);
    const [interactionId, setInteractionId] = useState(null);
    const [strategyLabel, setStrategyLabel] = useState(null);
    const [feedbackSent, setFeedbackSent] = useState(false);
    const [score, setScore] = useState(0);
    const [signalData, setSignalData] = useState({ nodes: [], edges: [] }); // Renamed to avoid collision with AbortSignal
    const [currentModality, setCurrentModality] = useState('Synthesis');
    const [ragSources, setRagSources] = useState([]);

    // Project ID: 25-26J-130: Hydration Guard for Cognitive Path
    useEffect(() => {
        if (signalData?.nodes?.length > 0 && !isVisualReady) {
            console.log(">>> [Hydration] Signal nodes detected, preparing visual flow...");
            // Small delay to ensure Mermaid has context if needed
            const timer = setTimeout(() => setIsVisualReady(true), 800);
            return () => clearTimeout(timer);
        }
    }, [signalData?.nodes, isVisualReady]);

    useEffect(() => {
        const initializeLesson = async (signal) => {
            if (!topic) return;
            setLoading(true);
            setIsThinking(true);
            setIsVisualReady(false); // Reset on new topic
            setSelectedOption(null);
            setIsSubmitted(false);
            setIsChallengeComplete(false);
            try {
                const topicId = topic.id || topic.title;
                // 0. Check for existing content
                const existing = await getLessonContent("student_001", topicId);

                if (signal.aborted) return;

                if (existing && (existing.content || existing.directive)) {
                    console.log(">>> [Persistence] Loading saved lesson state");
                    const savedDirective = existing.directive || existing.content;
                    setContent(savedDirective);
                    setIsThinking(false);
                    if (existing.user_response) {
                        setResponse(existing.user_response); // For Challenge
                    }
                    if (existing.ai_evaluation_score !== undefined) {
                        setScore(existing.ai_evaluation_score);
                        if (existing.ai_evaluation_score >= 0.7) setIsChallengeComplete(true);
                    }
                    setLoading(false);
                    onReady?.();
                    return;
                }

                const scenario = `Teach me about ${topic.title}`;
                const result = await runSimulation(scenario, topic);

                if (result.nodes) setSignalData({ nodes: result.nodes, edges: result.edges || [] });

                if (signal.aborted) return;

                if (result.meta?.strategy === 'ERROR' || result.meta?.strategy === 'TIMED_OUT') {
                    console.error(">>> [Synthesis Error]", result.meta?.error);
                    setError(result.meta?.body_text || "System is re-calibrating. Please wait a moment or try again.");
                    setIsThinking(false);
                    return;
                }

                // Extract directive from the best path
                const bestNodeId = result.meta?.best_path_ids?.[result.meta.best_path_ids.length - 1];
                const bestNode = result.nodes?.find(n => n.id === bestNodeId);

                // Content Payload Binding: Prioritize contextually rich content (Project ID: 25-26J-130)
                const directive = bestNode?.data?.directive || {
                    type: "explanation",
                    content: result.meta?.content?.full_text || result.meta?.body_text || result.meta?.final_response || "Concept synthesis complete."
                };

                setContent(directive);
                setInteractionId(result.meta?.interaction_id);
                setStrategyLabel(result.meta?.selected_strategy_label || result.meta?.strategy_label);
                setRagSources(result.meta?.rag_sources || []);
                setCurrentModality(result.meta?.current_modality || (directive?.content?.includes('graph TD') ? 'VISUAL' : 'TEXTUAL'));

                // ASYNC RENDER SYNCHRONIZATION
                if (directive && (directive.content || directive.full_text)) {
                    setTimeout(() => {
                        if (signal.aborted) return;
                        setIsThinking(false);
                        onReady?.();
                    }, 1500); // Visual effect
                } else {
                    console.error(">>> [Hydration] Synthesis returned empty content. Retrying...");
                    setError("Synthesis yielded empty content. Please try again.");
                    setIsThinking(false);
                }

            } catch (err) {
                if (err.name === 'AbortError') return;
                console.error(">>> [Lesson Init Error]", err);
                const message = err.response?.data?.detail || err.message || "Unknown error";
                setError(`Failed to initialize cognitive path: ${message}`);
            } finally {
                if (!signal.aborted) setLoading(false);
            }
        };

        const controller = new AbortController();
        initializeLesson(controller.signal);

        return () => {
            controller.abort();
        };
    }, [topic.id || topic.title]);

    const handleForceRegenerate = async () => {
        setIsThinking(true);
        setContent(null);
        setError(null);
        // Delete cache entry and re-run sim
        try {
            const topicId = topic.id || topic.title;
            // We don't have a direct delete API, so we just overwrite with null and re-run
            const scenario = `Teach me about ${topic.title}`;
            const result = await runSimulation(scenario, topic);
            const directive = result.nodes?.find(n => n.id === result.meta?.best_path_ids?.slice(-1)[0])?.data?.directive;
            setContent(directive);
            setIsThinking(false);
        } catch (e) {
            setError("Regeneration failed.");
        }
    };

    const hasDesignChallenge = useMemo(() => {
        const text = typeof content?.content === 'string' ? content.content : '';
        return text.includes('Design Challenge') || text.includes('### Challenge');
    }, [content, topic?.id]);

    const sanitizedContent = useMemo(() => {
        if (typeof content?.content !== 'string') return '';
        let text = content.content;

        // Remove Mermaid tags from Markdown flow (handled by DynamicVisualContainer)
        text = text.replace(/\[MERMAID_START\][\s\S]*?\[MERMAID_END\]/mg, '');

        // Handle [IMAGE_FOR_ALEX] - Convert to a visual hint or Mermaid-friendly block
        // In a real scenario, this would call an 'image_generation' API. 
        // For now, we'll transform it into a specialized visual indicator.
        text = text.replace(/\[IMAGE_FOR_ALEX\]/g, '\n\n> [!TIP]\n> **Visual Context Generated**: An specialized architectural snapshot has been generated for your learning profile Alex.\n\n');

        return text.trim();
    }, [content, topic?.id]);

    // Project ID: 25-26J-130: Mermaid Whitespace Stripper & Hidden Character Fix
    const mermaidData = useMemo(() => {
        if (!sanitizedContent || !sanitizedContent.includes('[MERMAID_START]')) return null;
        // Search original content to avoid stripped tags
        const originalText = typeof content?.content === 'string' ? content.content : '';
        const match = originalText.match(/\[MERMAID_START\]([\s\S]*?)\[MERMAID_END\]/);
        if (match && match[1]) {
            // Trim every line to remove hidden \r or non-breaking spaces
            return match[1]
                .split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0)
                .join('\n');
        }
        return null;
    }, [sanitizedContent, content?.content]);

    // Conditional Guard for empty content
    const isContentViewable = useMemo(() => {
        return !!(sanitizedContent || mermaidData || content?.type === 'quiz' || hasDesignChallenge || signalData?.nodes?.length > 0);
    }, [sanitizedContent, mermaidData, content, hasDesignChallenge, signalData?.nodes]);

    const isReadyToComplete = useMemo(() => {
        if (!isContentViewable) return false;
        if (mermaidData && !isVisualReady) return false; // HydrationGuard
        if (content?.type === 'quiz') return isSubmitted;
        if (hasDesignChallenge) return isChallengeComplete;
        return true;
    }, [content, isSubmitted, hasDesignChallenge, isChallengeComplete, isContentViewable, mermaidData, isVisualReady]);

    const handleComplete = async () => {
        if (!sessionId || !topic || isCompleting) return;
        setIsCompleting(true);
        try {
            // 1. Mark as completed
            await updateSessionProgress(sessionId, topic.title);

            // 2. Sync full lesson state to MongoDB
            const finalPayload = {
                student_id: "student_001",
                topic_id: topic.title,
                content: content,
                user_response: response,
                ai_evaluation_score: score
            };
            await saveLessonContent(finalPayload);
            await syncStudentProgress(finalPayload);

            // 3. Save Performance if quiz was attempted
            if (content?.type === 'quiz' && isSubmitted) {
                await savePerformance({
                    student_id: "student_001",
                    session_id: sessionId,
                    topic_id: topic.title,
                    score: selectedOption === content.quiz?.correct_index ? 100 : 0,
                    total_questions: 1,
                    correct_answers: selectedOption === content.quiz?.correct_index ? 1 : 0
                });
            }

            // 3. Navigate back
            onBack();
        } catch (err) {
            console.error("Completion Error:", err);
        } finally {
            setIsCompleting(false);
        }
    };

    const handleFeedback = async (sentiment) => {
        if (!interactionId || feedbackSent) return;
        setFeedbackSent(sentiment ? 'up' : 'down');
        try {
            const modality = (content?.type === 'visual_explanation' || sanitizedContent.includes('graph TD')) ? 'visual' : 'textual';
            await handleUserFeedback({
                student_id: "student_001",
                interaction_id: interactionId,
                action_type: strategyLabel || "SIMPLIFY_EXPLANATION",
                sentiment: sentiment,
                modality_type: modality,
                topic_id: topic?.title
            });
        } catch (err) {
            console.error("Feedback error:", err);
        }
    };

    if (error) return (
        <div className="h-full flex flex-col items-center justify-center p-10 text-center gap-6">
            <XCircle size={48} className="text-danger opacity-50" />
            <p className="text-zinc-500 dark:text-slate-400">{error}</p>
            <button onClick={onBack} className="text-primary font-bold uppercase tracking-widest text-xs">Return to Browser</button>
        </div>
    );

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark transition-colors overflow-y-auto custom-scrollbar">
            <div className="max-w-4xl mx-auto p-6 lg:p-12 min-h-full flex flex-col">

                {/* Header */}
                <header className="flex items-center justify-between mb-12">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 dark:text-slate-500 hover:text-primary transition-colors"
                    >
                        <ArrowLeft size={14} />
                        Exit Module
                    </button>
                    <div className="flex items-center gap-4">
                        {error && (
                            <button
                                onClick={handleForceRegenerate}
                                className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-danger hover:opacity-80 transition-opacity"
                            >
                                <Sparkles size={14} />
                                Force Regenerate
                            </button>
                        )}
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Live Synthesis Active</span>
                        </div>
                    </div>
                </header>

                <main className="flex-1 space-y-12 pb-24">
                    {isThinking ? (
                        <div className="h-[60vh] flex flex-col items-center justify-center gap-8 bg-white/40 dark:bg-white/[0.01] border border-edu-border-light dark:border-white/5 rounded-[40px] backdrop-blur-3xl shadow-sm transition-all">
                            <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                            <div className="space-y-2 text-center">
                                <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-primary animate-pulse">Orchestrating Knowledge Path</h3>
                                <p className="text-zinc-400 dark:text-slate-500 text-xs font-light tracking-wide">Synthesizing {topic?.title}...</p>
                            </div>
                        </div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-12"
                        >
                            <div className="space-y-4">
                                <h2 className="text-4xl lg:text-5xl font-light text-edu-text-light dark:text-white tracking-tight">
                                    {topic?.title}
                                </h2>
                                <div className="flex items-center gap-4 text-xs font-medium text-zinc-400 dark:text-slate-500 tracking-wide">
                                    <span className="flex items-center gap-1.5">
                                        <Gamepad2 size={14} />
                                        {strategyLabel ? `${strategyLabel.replace(/_/g, ' ')}` : 'INTERACTIVE NODE'}
                                    </span>
                                    <span className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-white/10" />
                                    <span className="flex items-center gap-1.5"><FileText size={14} /> {currentModality}</span>
                                </div>
                            </div>

                            <article className="prose prose-lg dark:prose-invert prose-indigo max-w-none">
                                <div className="text-xl font-light leading-relaxed text-zinc-600 dark:text-slate-300 transition-colors">
                                    <ReactMarkdown components={{
                                        code({ node, inline, className, children, ...props }) {
                                            return (
                                                <code className="bg-primary/20 text-white px-2 py-0.5 rounded text-sm font-mono border border-primary/30" {...props}>
                                                    {children}
                                                </code>
                                            )
                                        },
                                        p: ({ children }) => <p className="mb-6 leading-relaxed opacity-90">{children}</p>,
                                        h3: ({ children }) => <h3 className="text-2xl font-light text-primary mt-12 mb-6 tracking-tight">{children}</h3>,
                                        li: ({ children }) => <li className="mb-3 list-disc ml-6 opacity-80">{children}</li>,
                                        strong: ({ children }) => <strong className="font-bold text-white border-b border-primary/30">{children}</strong>
                                    }}>
                                        {sanitizedContent}
                                    </ReactMarkdown>
                                </div>
                            </article>

                            {/* ComponentFactory: Dynamic Hydration Layer */}
                            {mermaidData && (
                                <div className="my-12 p-8 bg-[#121212]/50 rounded-[40px] border border-white/5 shadow-2xl overflow-hidden group transition-all hover:border-primary/20">
                                    <div className="flex items-center gap-3 mb-8">
                                        <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                            <span className="text-[10px] font-black text-primary">VIS</span>
                                        </div>
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400">Architectural Schema</h4>
                                    </div>
                                    <Mermaid chart={mermaidData} />
                                </div>
                            )}

                            {hasDesignChallenge && (
                                <ErrorBoundary onMountFailure={handleForceRegenerate}>
                                    <ChallengeComponent
                                        topic={topic?.title}
                                        context={content?.content}
                                        sessionId={sessionId}
                                        onComplete={(userRes, evaluationScore) => {
                                            setIsChallengeComplete(true);
                                            setResponse(userRes);
                                            setScore(evaluationScore);
                                        }}
                                    />
                                </ErrorBoundary>
                            )}

                            {content?.type === 'quiz' && (
                                <ErrorBoundary onMountFailure={handleForceRegenerate}>
                                    <QuizComponent
                                        quiz={content.quiz}
                                        selectedOption={selectedOption}
                                        onOptionSelect={setSelectedOption}
                                        isSubmitted={isSubmitted}
                                        correctIndex={content.quiz?.correct_index}
                                    />
                                </ErrorBoundary>
                            )}

                            {content?.type === 'quiz' && !isSubmitted && selectedOption !== null && (
                                <button
                                    onClick={() => setIsSubmitted(true)}
                                    className="w-full py-5 bg-primary text-white font-black rounded-full shadow-2xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all text-xs uppercase tracking-[0.3em]"
                                >
                                    Verify Knowledge knowledge
                                </button>
                            )}

                            <div className="pt-12 border-t border-edu-border-light dark:border-white/5 flex flex-col items-center gap-8">
                                {/* Feedback Section (Project ID: 25-26J-130) */}
                                <div className="flex flex-col items-center gap-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">How was this explanation?</p>
                                    <div className="flex items-center gap-6">
                                        <button
                                            onClick={() => handleFeedback(true)}
                                            disabled={feedbackSent}
                                            className={clsx(
                                                "p-4 rounded-full border transition-all hover:scale-110 active:scale-95",
                                                feedbackSent === 'up' ? "bg-secondary/20 border-secondary text-secondary" : "bg-white/5 border-white/10 text-zinc-400 hover:border-secondary/50"
                                            )}
                                        >
                                            <Sparkles size={20} />
                                        </button>
                                        <button
                                            onClick={() => handleFeedback(false)}
                                            disabled={feedbackSent}
                                            className={clsx(
                                                "p-4 rounded-full border transition-all hover:scale-110 active:scale-95",
                                                feedbackSent === 'down' ? "bg-danger/20 border-danger text-danger" : "bg-white/5 border-white/10 text-zinc-400 hover:border-danger/50"
                                            )}
                                        >
                                            <XCircle size={20} />
                                        </button>
                                    </div>
                                    {feedbackSent && (
                                        <motion.p
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            className="text-[10px] text-zinc-500 italic"
                                        >
                                            Thank you! Your feedback helps refine your learning path.
                                        </motion.p>
                                    )}
                                </div>

                                <div className="flex items-center gap-3 opacity-50">
                                    <Database size={16} className="text-zinc-400" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Persistent Cognition Layer Active</span>
                                </div>

                                <AnimatePresence>
                                    {isReadyToComplete && (
                                        <motion.button
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            onClick={handleComplete}
                                            disabled={isCompleting}
                                            className="group relative px-16 py-6 bg-secondary text-white font-black rounded-full shadow-2xl shadow-secondary/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 flex items-center gap-3 overflow-hidden"
                                        >
                                            <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                                            <span className="relative z-10 uppercase tracking-[0.3em] text-xs">
                                                {isCompleting ? 'Synchronizing...' : 'Complete Module'}
                                            </span>
                                            <CheckCircle2 size={18} className="relative z-10" />
                                        </motion.button>
                                    )}
                                </AnimatePresence>

                                {/* Project ID: 25-26J-130: Knowledge Sources Footer */}
                                {ragSources?.length > 0 && (
                                    <div className="mt-12 w-full pt-12 border-t border-edu-border-light dark:border-white/5">
                                        <div className="flex flex-col gap-4">
                                            <div className="flex items-center gap-2">
                                                <Database size={14} className="text-secondary" />
                                                <span className="text-[10px] font-black uppercase tracking-widest text-secondary">Verified Knowledge Sources</span>
                                            </div>
                                            <div className="flex flex-wrap gap-3">
                                                {Array.from(new Set(ragSources)).map((src, idx) => (
                                                    <div key={idx} className="px-4 py-2 bg-secondary/5 border border-secondary/10 rounded-full flex items-center gap-2 text-[10px] text-zinc-500 font-medium lowercase">
                                                        <FileText size={12} className="opacity-50" />
                                                        {src}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default LessonView;
