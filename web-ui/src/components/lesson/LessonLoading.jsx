import React from 'react';
import { Bot } from 'lucide-react';

const LessonLoading = ({ topicTitle }) => {
    return (
        <div className="h-full w-full flex items-center justify-center bg-edu-bg-light dark:bg-edu-bg-dark">
            <div className="flex flex-col items-center gap-6">
                <div className="relative">
                    <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Bot size={24} className="text-primary animate-pulse" />
                    </div>
                </div>
                <div className="text-center space-y-2">
                    <h2 className="text-xl font-light text-edu-text-light dark:text-white tracking-tight uppercase">Initializing Cognitive Path...</h2>
                    <p className="text-xs text-zinc-500 font-mono tracking-widest">{topicTitle}</p>
                </div>
            </div>
        </div>
    );
};

export default LessonLoading;
