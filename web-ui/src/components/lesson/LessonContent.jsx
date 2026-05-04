import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Gamepad2, FileText, Database } from 'lucide-react';
import Mermaid from '../Mermaid';
import DynamicVisualContainer from '../DynamicVisualContainer';

const LessonContent = ({ 
    topic, 
    isFromCache, 
    strategyLabel, 
    currentModality, 
    sanitizedContent, 
    mermaidData, 
    hasDesignChallenge, 
    content, 
    sessionId, 
    setIsChallengeComplete, 
    setResponse, 
    setScore, 
    selectedOption, 
    setSelectedOption, 
    isSubmitted, 
    setIsSubmitted, 
    ragSources,
    ChallengeComponent,
    QuizComponent,
    ErrorBoundary
}) => {
    return (
        <div className="space-y-12">
            <div className="space-y-4">
                <div className="flex items-center gap-4">
                    <h2 className="text-4xl lg:text-5xl font-light text-edu-text-light dark:text-white tracking-tight">{topic?.title}</h2>
                    {isFromCache && (
                        <span className="px-3 py-1 bg-secondary/20 border border-secondary/30 text-secondary text-[10px] font-black uppercase tracking-widest rounded-full">
                            Previously Completed
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-4 text-xs font-medium text-zinc-400 dark:text-slate-500 tracking-wide">
                    <span className="flex items-center gap-1.5"><Gamepad2 size={14} /> {strategyLabel?.replace(/_/g, ' ') || 'INTERACTIVE NODE'}</span>
                    <span className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-white/10" />
                    <span className="flex items-center gap-1.5"><FileText size={14} /> {currentModality}</span>
                </div>
            </div>

            <article className="prose prose-lg dark:prose-invert prose-indigo max-w-none">
                <div className="text-xl font-light leading-relaxed text-zinc-600 dark:text-slate-300 transition-colors">
                    <ReactMarkdown components={{
                        code({ node, inline, className, children, ...props }) {
                            return <code className="bg-primary/20 text-white px-2 py-0.5 rounded text-sm font-mono border border-primary/30" {...props}>{children}</code>
                        },
                        p: ({ children }) => <p className="mb-6 leading-relaxed opacity-90">{children}</p>,
                        h3: ({ children }) => <h3 className="text-2xl font-light text-primary mt-12 mb-6 tracking-tight">{children}</h3>,
                        li: ({ children }) => <li className="mb-3 list-disc ml-6 opacity-80">{children}</li>,
                        strong: ({ children }) => <strong className="font-bold text-white border-b border-primary/30">{children}</strong>
                    }}>{sanitizedContent}</ReactMarkdown>
                </div>
            </article>

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
                <ErrorBoundary>
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
                <ErrorBoundary>
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
                <button onClick={() => setIsSubmitted(true)} className="w-full py-5 bg-primary text-white font-black rounded-full shadow-2xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all text-xs uppercase tracking-[0.3em]">
                    Verify Knowledge
                </button>
            )}

            {ragSources?.length > 0 && (
                <div className="mt-12 w-full pt-12 border-t border-edu-border-light dark:border-white/5">
                    <div className="flex flex-col gap-4">
                        <div className="flex items-center gap-2">
                            <Database size={14} className="text-secondary" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-secondary">Verified Knowledge Sources</span>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {Array.from(new Set(ragSources)).map((src, idx) => (
                                <div key={idx} className="px-4 py-2 bg-secondary/5 border border-secondary/10 rounded-full flex items-center gap-2 text-[10px] text-zinc-500 font-medium">
                                    <FileText size={12} className="opacity-50" /> {src}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LessonContent;
