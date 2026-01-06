import React, { useState, useEffect } from 'react';
import { Copy, Check, FileText, ArrowLeft, PlayCircle, Cpu, Code } from 'lucide-react';

const ContentGeneration = ({ request, onBack, onStartLearning }) => {
    const [copied, setCopied] = useState(false);
    const [generatedContent, setGeneratedContent] = useState(null);

    // Simulate Generation Delay on Mount
    useEffect(() => {
        // Deterministic Simulation Logic based on Request
        const generate = () => {
            const { selectedStrategy, studentPersona, outputSpec, topic } = request;
            const tone = selectedStrategy.tone?.toLowerCase() || 'neutral';

            let content = {
                title: `Learning Module: ${topic?.title || 'Unknown Topic'}`,
                intro: '',
                main: '',
                practice: '',
                summary: ''
            };

            // 1. Intro
            if (tone.includes('socratic') || outputSpec.style === 'interactive') {
                content.intro = `Hi ${studentPersona.name}, let's explore this together. What do you already know about ${topic.title}?`;
            } else if (tone.includes('direct') || tone.includes('authoritative')) {
                content.intro = `Objective: Master the core concepts of ${topic.title}.`;
            } else {
                content.intro = `Welcome, ${studentPersona.name}. Today we're diving into ${topic.title}.`;
            }

            // 2. Main Body (Simulation)
            if (selectedStrategy.techniques.includes('Metaphor')) {
                content.main = `Imagine ${topic.title} is like a vast network of rivers... (Metaphorical explanation driven by ${selectedStrategy.pathTitle})`;
            } else if (selectedStrategy.techniques.includes('Code')) {
                content.main = `Let's look at the implementation details using Python...`;
            } else {
                content.main = `Here are the key takeaways based on your learning profile (${studentPersona.type})...`;
            }

            // 3. Practice
            content.practice = `Try this ${outputSpec.length} exercise to test your understanding.`;

            // 4. Summary
            content.summary = `Great job reaching the end of this ${outputSpec.length} session.`;

            setGeneratedContent(content);
        };

        // Small fake delay for "Generation" effect
        const timer = setTimeout(generate, 800);
        return () => clearTimeout(timer);

    }, [request]);

    const handleCopy = () => {
        navigator.clipboard.writeText(JSON.stringify(request, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!request) return <div className="p-10 text-slate-500">No Generation Request Found.</div>;

    return (
        <div className="flex h-full w-full bg-slate-950 text-slate-100 p-6 gap-6 transition-all animate-in fade-in duration-700">

            {/* LEFT COLUMN: Context & JSON */}
            <div className="w-1/3 flex flex-col gap-6">

                {/* Strategy Summary Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Cpu size={64} />
                    </div>
                    <h2 className="text-sm font-bold uppercase tracking-widest text-indigo-400 mb-4 flex items-center gap-2">
                        <Cpu size={14} /> Selected Strategy
                    </h2>
                    <div className="text-2xl font-light mb-2">{request.selectedStrategy.pathTitle || 'Adaptive Strategy'}</div>
                    <div className="flex flex-wrap gap-2 mb-4">
                        {request.selectedStrategy.techniques?.map(t => (
                            <span key={t} className="px-2 py-1 rounded bg-indigo-500/20 text-indigo-300 text-xs border border-indigo-500/30">
                                {t}
                            </span>
                        ))}
                    </div>
                    <div className="text-slate-400 text-sm">
                        Targeting <b>{request.studentPersona.name}</b> with a <b>{request.selectedStrategy.tone}</b> tone.
                    </div>
                </div>

                {/* JSON Payload Panel */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl flex-1 flex flex-col shadow-xl overflow-hidden">
                    <div className="bg-slate-950/50 p-3 border-b border-slate-800 flex items-center justify-between">
                        <span className="text-xs font-mono text-slate-500 flex items-center gap-2">
                            <Code size={12} /> generator_request.json
                        </span>
                        <button onClick={handleCopy} className="text-slate-500 hover:text-white transition-colors">
                            {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                        </button>
                    </div>
                    <div className="flex-1 overflow-auto p-4 relative group">
                        <pre className="text-[10px] font-mono text-emerald-100/70 leading-relaxed whitespace-pre-wrap">
                            {JSON.stringify(request, null, 2)}
                        </pre>
                    </div>
                </div>
            </div>

            {/* RIGHT COLUMN: Generated Content */}
            <div className="flex-1 flex flex-col bg-slate-100 text-slate-900 rounded-2xl shadow-2xl overflow-hidden relative">
                {/* Header */}
                <div className="bg-white p-6 border-b border-slate-200 flex items-center justify-between">
                    <div>
                        <div className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Generated Output</div>
                        <h1 className="text-2xl font-serif text-slate-800">Learning Session Preview</h1>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={onBack} className="px-4 py-2 rounded-lg text-slate-500 hover:bg-slate-100 font-medium text-sm flex items-center gap-2 transition-colors">
                            <ArrowLeft size={16} /> Strategy
                        </button>
                        <button onClick={onStartLearning} className="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-500/30 transition-all hover:scale-105">
                            <PlayCircle size={16} /> Start Learning
                        </button>
                    </div>
                </div>

                {/* Document Body */}
                <div className="flex-1 overflow-y-auto p-12 bg-white">
                    {generatedContent ? (
                        <div className="max-w-3xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
                            {/* Title Section */}
                            <div className="pb-6 border-b border-slate-100">
                                <span className="text-indigo-600 font-bold tracking-wider text-xs uppercase mb-2 block">Module 1.0</span>
                                <h2 className="text-4xl font-serif text-slate-900 mb-4">{generatedContent.title}</h2>
                                <p className="text-lg text-slate-600 italic font-serif leading-relaxed">"{generatedContent.intro}"</p>
                            </div>

                            {/* Content Blocks */}
                            <div className="prose prose-slate max-w-none">
                                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                    <FileText size={18} className="text-indigo-500" /> Core Concept
                                </h3>
                                <p className="text-slate-600 leading-7">{generatedContent.main}</p>

                                <div className="my-8 p-6 bg-slate-50 rounded-xl border-l-4 border-indigo-500">
                                    <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2">Key Insight</h4>
                                    <p className="text-slate-700">The strategy selected ({request.selectedStrategy.pathTitle}) optimized for this specific explanation style.</p>
                                </div>

                                <h3 className="text-lg font-bold text-slate-900 mt-8">Practice</h3>
                                <p className="text-slate-600">{generatedContent.practice}</p>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4">
                            <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
                            <span className="text-sm font-medium animate-pulse">Synthesizing personalized content...</span>
                        </div>
                    )}
                </div>

            </div>

        </div>
    );
};

export default ContentGeneration;
