import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { XCircle, Sparkles, BrainCircuit } from 'lucide-react';
import { useLessonData } from '../components/lesson/useLessonData';
import LessonHeader from '../components/lesson/LessonHeader';
import LessonContent from '../components/lesson/LessonContent';
import LessonFeedback from '../components/lesson/LessonFeedback';
import LessonLoading from '../components/lesson/LessonLoading';
import ChallengeComponent from '../components/lesson/ChallengeComponent';
import QuizComponent from '../components/lesson/QuizComponent';
import ErrorBoundary from '../components/lesson/ErrorBoundary';

const LessonView = ({ sessionId, topic, onBack, onReady, sio, onPrefetchStarted }) => {
    const data = useLessonData(sessionId, topic, onBack, onReady, sio, onPrefetchStarted);

    if (data.error) return (
        <div className="h-full flex flex-col items-center justify-center p-10 text-center gap-6 bg-edu-bg-light dark:bg-edu-bg-dark">
            <XCircle size={48} className="text-danger opacity-50" />
            <p className="text-zinc-500 dark:text-slate-400">{data.error}</p>
            <button onClick={onBack} className="text-primary font-bold uppercase tracking-widest text-xs">Return to Browser</button>
        </div>
    );

    if (data.isThinking && !data.isContentViewable) {
        return <LessonLoading topicTitle={topic?.title} />;
    }

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark transition-colors overflow-y-auto custom-scrollbar">
            <div className="max-w-4xl mx-auto p-6 lg:p-12 min-h-full flex flex-col">
                <LessonHeader onBack={onBack} strategyLabel={data.strategyLabel} currentModality={data.currentModality} />

                <main className="flex-1 space-y-12 pb-24">
                    {!data.isContentViewable ? (
                        <div className="h-[40vh] flex flex-col items-center justify-center p-8 bg-white/40 dark:bg-white/[0.01] border border-edu-border-light dark:border-white/5 rounded-[48px] backdrop-blur-3xl shadow-sm transition-all overflow-hidden relative">
                             <div className="w-10 h-10 border-[3px] border-primary/10 border-t-primary rounded-full animate-spin" />
                             <p className="mt-4 text-[10px] font-black uppercase tracking-widest text-primary animate-pulse">Initializing Cognitive Path...</p>
                        </div>
                    ) : (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                            <LessonContent 
                                topic={topic}
                                isFromCache={data.isFromCache}
                                strategyLabel={data.strategyLabel}
                                currentModality={data.currentModality}
                                sanitizedContent={data.sanitizedContent}
                                mermaidData={data.mermaidData}
                                hasDesignChallenge={data.hasDesignChallenge}
                                content={data.content}
                                sessionId={sessionId}
                                setIsChallengeComplete={data.setIsChallengeComplete}
                                setResponse={data.setResponse}
                                setScore={data.setScore}
                                selectedOption={data.selectedOption}
                                setSelectedOption={data.setSelectedOption}
                                isSubmitted={data.isSubmitted}
                                setIsSubmitted={data.setIsSubmitted}
                                ragSources={data.ragSources}
                                ChallengeComponent={ChallengeComponent}
                                QuizComponent={QuizComponent}
                                ErrorBoundary={ErrorBoundary}
                            />

                            <LessonFeedback 
                                feedbackSent={data.feedbackSent}
                                onFeedback={data.handleFeedback}
                                isReadyToComplete={data.isReadyToComplete}
                                isCompleting={data.isCompleting}
                                handleComplete={data.handleComplete}
                                isContentViewable={data.isContentViewable}
                                isFromCache={data.isFromCache}
                            />
                        </motion.div>
                    )}
                </main>

                {/* Suggestions & Profile Adaptation Toasts */}
                <div className="fixed bottom-12 right-12 z-[100] flex flex-col gap-4 items-end">
                    <AnimatePresence>
                        {data.shadowReady && (
                            <motion.div initial={{ opacity: 0, y: 20, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 20, scale: 0.9 }} className="p-6 bg-zinc-900 border border-secondary/30 backdrop-blur-3xl rounded-[32px] shadow-2xl flex items-center justify-between gap-6 max-w-md">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-secondary/10 flex items-center justify-center text-secondary border border-secondary/20"><Sparkles size={24} /></div>
                                    <div className="text-left">
                                        <p className="text-[10px] font-black uppercase tracking-widest text-secondary">Alternative Path Ready</p>
                                        <p className="text-sm font-light text-zinc-300">Switch to <strong>{data.shadowReady.alternative_label}</strong> for better engagement?</p>
                                    </div>
                                </div>
                                <div className="flex flex-col gap-2">
                                    <button onClick={data.handleAcceptShadow} className="px-6 py-3 bg-secondary text-white text-[10px] font-black uppercase tracking-widest rounded-full hover:scale-105 active:scale-95 transition-all">Swap</button>
                                    <button onClick={data.handleDismissShadow} className="text-[9px] font-bold text-zinc-500 uppercase tracking-tighter hover:text-zinc-300 transition-colors">Dismiss</button>
                                </div>
                            </motion.div>
                        )}

                        {data.profileToast && (
                            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="p-6 bg-zinc-900/90 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-3xl text-white flex items-center gap-4 min-w-[320px]">
                                <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center border border-secondary/40"><BrainCircuit className="text-secondary" /></div>
                                <div className="text-left">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-secondary mb-1">Profile Adapted</p>
                                    <p className="text-xs font-light text-zinc-400">Increased <strong>{data.profileToast.modality}</strong> weight by <strong>+{data.profileToast.delta}</strong></p>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default LessonView;
