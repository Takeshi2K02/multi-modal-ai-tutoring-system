import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import clsx from 'clsx';

const ThoughtNode = ({ data, isConnectable }) => {
    const { label, localScore, pathScore, type, isBestPath, depth, metadata, isSynthesisComplete } = data;
    const { strategy_name, internal_thought, pruning_status } = metadata || {};

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

    const isWinningPath = isBestPath;
    const isBeamSelected = pruning_status === 'Selected';
    const isBeamCandidate = pruning_status === 'Beam';

    const wrapperClasses = clsx(
        "relative flex flex-col font-sans transition-all duration-500 rounded-3xl backdrop-blur-3xl bg-[#141414]/95 border-2 shadow-2xl font-semibold",
        baseBorderColor,
        isWinningPath
            ? "border-[#00f2ff] ring-2 ring-[#00AFB9]/50 scale-105 z-[100] shadow-[0_0_40px_rgba(0,242,255,0.4),0_0_15px_#00f2ff] opacity-100"
            : isBeamSelected && !isSynthesisComplete
                ? "border-[#00f2ff] ring-1 ring-[#00AFB9]/30 scale-[1.02] z-10 opacity-100 shadow-[0_0_20px_rgba(0,242,255,0.2)]"
                : isBeamCandidate && !isSynthesisComplete
                    ? "border-[#00f2ff]/30 opacity-100 z-10"
                    : "border-white/5 opacity-60 grayscale-[40%] hover:opacity-100 hover:grayscale-0 hover:scale-105 hover:border-white/20"
    );

    const SelectionBadge = isWinningPath && !isRoot ? (
        <div className="absolute -top-3 -right-3 bg-[#00f2ff] text-black text-[9px] font-black px-4 py-2 rounded-full shadow-[0_0_20px_rgba(0,242,255,0.6)] animate-pulse z-20 flex items-center gap-1.5 border border-white/20">
            <div className="w-1.5 h-1.5 rounded-full bg-black shadow-[0_0_5px_black]" />
            BEST PATH
        </div>
    ) : isBeamSelected && !isRoot && !isSynthesisComplete ? (
        <div className="absolute -top-3 -right-3 bg-[#00f2ff] text-black text-[8px] font-black px-3 py-1.5 rounded-full shadow-[0_0_15px_rgba(0,242,255,0.4)] z-20 border border-white/20">
            CHOSEN
        </div>
    ) : null;

    const StatusBadge = pruning_status ? (
        <div className={clsx(
            "px-2 py-0.5 rounded-full text-[7px] font-black uppercase tracking-tighter border",
            pruning_status === "Selected" ? "bg-primary/20 text-primary border-primary/30" :
                pruning_status === "Beam" ? "bg-[#48CAE4]/20 text-[#48CAE4] border-[#48CAE4]/30" :
                    pruning_status === "Pruned" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                        "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
        )}>
            {pruning_status}
        </div>
    ) : null;

    return (
        <div className={wrapperClasses} style={{ width: '350px', height: 'auto' }}>
            {SelectionBadge}
            <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-white/20 !border-white/10" isConnectable={isConnectable} />

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-black/60 transition-colors">
                <div className="flex flex-col gap-0.5">
                    <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-white line-clamp-1 text-shadow-sm">
                        {strategy_name || type || "Thought"}
                    </span>
                    <div className="flex items-center gap-1.5">
                        {StatusBadge}
                        {!isRoot && type !== 'final' && (
                            <span className="text-[7px] font-black text-secondary uppercase tracking-widest opacity-80">
                                STRATEGY BLUEPRINT
                            </span>
                        )}
                    </div>
                </div>
                <div className={clsx("px-2.5 py-1 rounded-full text-[10px] font-bold flex items-center gap-1.5 border shrink-0 text-white shadow-[0_0_10px_rgba(0,242,255,0.3)]", scoreStyles)}>
                    <div className="w-1.5 h-1.5 rounded-full bg-current shadow-[0_0_8px_currentColor]" />
                    <span className="font-bold [text-shadow:_0_0_5px_rgba(0,242,255,0.5)]">{localScore?.toFixed(2) ?? "N/A"}</span>
                </div>
            </div>

            {/* Body */}
            <div className="p-4 relative">
                {isBestPath && <div className="absolute inset-0 bg-[#00AFB9]/5 pointer-events-none" />}
                <div className="relative z-10 space-y-3">
                    <div className="space-y-1">
                        <span className="text-[8px] font-bold text-white uppercase tracking-widest opacity-90">Reasoning Log</span>
                        <p className="text-xs font-semibold text-white leading-relaxed tracking-tight transition-colors whitespace-pre-wrap">
                            {internal_thought || label}
                        </p>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-2.5 bg-black/60 flex items-center justify-between text-[9px] text-white border-t border-white/10 transition-colors">
                <div className="flex flex-col">
                    <span className="font-bold uppercase tracking-widest opacity-70 text-white">Path Score</span>
                    <span className={clsx("font-black tracking-widest", isBestPath ? "text-[#00f2ff]" : "text-white")}>
                        {pathScore?.toFixed(2) ?? "0.00"}
                    </span>
                </div>
                <div className="flex flex-col text-right">
                    <span className="font-bold uppercase tracking-widest opacity-50">Depth</span>
                    <span className="font-black tracking-widest text-[#48CAE4]">{depth}</span>
                </div>
            </div>

            <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-white/20 !border-white/10" isConnectable={isConnectable} />
        </div>
    );
};

export default memo(ThoughtNode);
