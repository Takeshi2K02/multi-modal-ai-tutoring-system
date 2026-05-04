import React from 'react';
import { ArrowLeft, Gamepad2, FileText } from 'lucide-react';

const LessonHeader = ({ onBack, strategyLabel, currentModality }) => {
    return (
        <header className="flex items-center justify-between mb-12">
            <button 
                onClick={onBack} 
                className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 dark:text-slate-500 hover:text-primary transition-colors"
            >
                <ArrowLeft size={14} /> Exit Module
            </button>
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Live Synthesis Active</span>
                </div>
            </div>
        </header>
    );
};

export default LessonHeader;
