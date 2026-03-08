import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import clsx from 'clsx';

const ThoughtNode = ({ data, isConnectable }) => {
    const { label, localScore, pathScore, type, isBestPath, depth } = data;

    // Strict Deep Oceanic Status Scale (ID: 25-26J-130)
    // SUCCESS: #00AFB9 | STRATEGY SHIFT: #48CAE4 | FRUSTRATION: #F07167
    const scoreStyles = localScore >= 0.8
        ? 'text-[#00AFB9] bg-[#00AFB9]/10 border-[#00AFB9]/30'
        : localScore >= 0.5
            ? 'text-[#48CAE4] bg-[#48CAE4]/10 border-[#48CAE4]/30'
            : 'text-[#F07167] bg-[#F07167]/10 border-[#F07167]/30';

    const baseBorderColor = localScore >= 0.8
        ? 'border-t-[#00AFB9]/50'
        : localScore >= 0.5
            ? 'border-t-[#48CAE4]/50'
            : 'border-t-[#F07167]/50';

    const isRoot = depth === 0;

    const wrapperClasses = clsx(
        "relative flex flex-col font-sans border-t-2 transition-all duration-500 rounded-3xl overflow-hidden backdrop-blur-3xl bg-white dark:bg-[#1E293B]/80 border border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl",
        baseBorderColor,
        isBestPath ? "ring-2 ring-[#00AFB9]/50 scale-105 z-10 shadow-[0_0_40px_rgba(72,202,228,0.2)]" : (!isRoot && "opacity-40 grayscale-[0.8] hover:opacity-100 hover:grayscale-0 hover:scale-105")
    );

    const SelectionBadge = isBestPath && !isRoot ? (
        <div className="absolute -top-3 -right-3 bg-[#00AFB9] text-white text-[8px] font-black px-3 py-1.5 rounded-full shadow-[0_0_20px_rgba(0,175,185,0.5)] animate-pulse z-20">
            CHOSEN
        </div>
    ) : null;

    const directive = data.directive;
    const DirectiveInfo = directive ? (
        <div className="mb-3 flex flex-wrap gap-1.5">
            <span className="px-2 py-0.5 rounded-full bg-[#0077B6]/20 text-[#0077B6] text-[8px] font-black uppercase tracking-widest border border-[#0077B6]/30">
                {directive.type}
            </span>
            {directive.parameters?.tone && (
                <span className="px-2 py-0.5 rounded-full bg-zinc-50 dark:bg-white/5 text-zinc-500 dark:text-slate-400 text-[8px] font-bold tracking-wider border border-edu-border-light dark:border-white/10 uppercase transition-colors">
                    {directive.parameters.tone}
                </span>
            )}
        </div>
    ) : null;

    return (
        <div className={wrapperClasses} style={{ width: '220px' }}>
            {SelectionBadge}
            <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-white/20 !border-white/10" isConnectable={isConnectable} />

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-edu-border-light dark:border-[#90E0EF]/10 bg-white/50 dark:bg-[#1E293B]/40 transition-colors">
                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-400 dark:text-slate-500">
                    {type || "Thought"}
                </span>
                <div className={clsx("px-2.5 py-1 rounded-full text-[9px] font-black flex items-center gap-1.5 border", scoreStyles)}>
                    <div className="w-1.5 h-1.5 rounded-full bg-current shadow-[0_0_8px_currentColor]" />
                    {localScore?.toFixed(2) ?? "N/A"}
                </div>
            </div>

            {/* Body */}
            <div className="p-4 relative min-h-[60px]">
                {isBestPath && <div className="absolute inset-0 bg-[#00AFB9]/5 pointer-events-none" />}
                <div className="relative z-10">
                    {DirectiveInfo}
                    <p className="text-xs font-light text-edu-text-light dark:text-[#CAF0F8] leading-relaxed tracking-tight transition-colors">
                        {label}
                    </p>
                </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-2.5 bg-white/50 dark:bg-[#1E293B]/40 flex items-center justify-between text-[9px] text-zinc-400 dark:text-slate-500 border-t border-edu-border-light dark:border-[#90E0EF]/10 transition-colors">
                <span className="font-bold uppercase tracking-widest opacity-50">Path Score</span>
                <span className={clsx("font-black tracking-widest", isBestPath ? "text-[#00AFB9]" : "text-zinc-400 dark:text-slate-400")}>
                    {pathScore?.toFixed(2) ?? "0.00"}
                </span>
            </div>

            <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-white/20 !border-white/10" isConnectable={isConnectable} />
        </div>
    );
};

export default memo(ThoughtNode);
