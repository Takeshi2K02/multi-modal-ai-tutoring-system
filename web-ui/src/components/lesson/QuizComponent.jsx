import React from 'react';
import { Sparkles, BrainCircuit, CheckCircle2, XCircle, FileText, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const QuizComponent = ({ quiz, onOptionSelect, isSubmitted, selectedOption, correctIndex }) => {
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

export default QuizComponent;
