import React from 'react';
import { ThumbsUp, ThumbsDown, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';

const LessonFeedback = ({ 
    feedbackSent, 
    onFeedback, 
    isReadyToComplete, 
    isCompleting, 
    handleComplete, 
    isContentViewable,
    isFromCache
}) => {
    const thumbsUpClass = clsx(
        "p-4 rounded-full border transition-all duration-300", 
        feedbackSent === 'up' 
            ? "bg-secondary border-secondary text-white shadow-xl shadow-secondary/40 scale-110" 
            : feedbackSent 
                ? "opacity-20 grayscale cursor-not-allowed" 
                : "bg-white/5 border-white/10 text-zinc-400 hover:border-secondary/50 hover:scale-110 active:scale-95"
    );

    const thumbsDownClass = clsx(
        "p-4 rounded-full border transition-all duration-300", 
        feedbackSent === 'down' 
            ? "bg-danger border-danger text-white shadow-xl shadow-danger/40 scale-110" 
            : feedbackSent 
                ? "opacity-20 grayscale cursor-not-allowed" 
                : "bg-white/5 border-white/10 text-zinc-400 hover:border-danger/50 hover:scale-110 active:scale-95"
    );

    const isActionable = isReadyToComplete || isFromCache;

    const completeButtonClass = clsx(
        "w-full py-6 rounded-full font-black text-xs uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-4 shadow-2xl",
        isActionable 
            ? "bg-secondary text-white shadow-secondary/30 hover:scale-[1.02] active:scale-95" 
            : "bg-white/5 text-zinc-600 cursor-not-allowed opacity-50 border border-white/5"
    );

    return (
        <div className="pt-12 border-t border-edu-border-light dark:border-white/5 flex flex-col items-center gap-8">
            {!isFromCache && (
                <div className="flex flex-col items-center gap-4">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">How was this explanation?</p>
                    <div className="flex items-center gap-6">
                        <button 
                            onClick={() => onFeedback(true)} 
                            disabled={feedbackSent} 
                            className={thumbsUpClass}
                        >
                            <ThumbsUp size={20} fill={feedbackSent === 'up' ? "currentColor" : "none"} />
                        </button>
                        <button 
                            onClick={() => onFeedback(false)} 
                            disabled={feedbackSent} 
                            className={thumbsDownClass}
                        >
                            <ThumbsDown size={20} fill={feedbackSent === 'down' ? "currentColor" : "none"} />
                        </button>
                    </div>
                </div>
            )}

            <div className="w-full max-w-md flex flex-col items-center gap-4">
                <button 
                    onClick={handleComplete} 
                    disabled={isCompleting || (!isReadyToComplete && !isFromCache)}
                    className={completeButtonClass}
                >
                    {isCompleting ? 'Synchronizing State...' : (isFromCache ? 'Return to Path' : 'Complete Module')}
                    <CheckCircle2 size={18} />
                </button>
                
                {!feedbackSent && isContentViewable && !isFromCache && (
                    <p className="text-[10px] font-medium text-zinc-500 animate-pulse">
                        Please rate this explanation to continue
                    </p>
                )}
            </div>
        </div>
    );
};

export default LessonFeedback;
