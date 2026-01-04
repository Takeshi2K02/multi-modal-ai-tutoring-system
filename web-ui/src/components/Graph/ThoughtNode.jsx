import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import clsx from 'clsx';

const ThoughtNode = ({ data, isConnectable }) => {
    const { label, localScore, pathScore, type, isBestPath, depth } = data;

    const scoreColor = localScore >= 0.8 ? 'text-emerald-600 bg-emerald-50'
        : localScore >= 0.5 ? 'text-amber-600 bg-amber-50'
            : 'text-rose-600 bg-rose-50';

    // Base border color based on score alone
    const baseBorderColor = localScore >= 0.8 ? 'border-t-emerald-500'
        : localScore >= 0.5 ? 'border-t-amber-500'
            : 'border-t-rose-500';

    // Dynamic classes based on selection (Best Path)
    // If it's the best path, we force a strong highlight.
    // If not, and it's not root, we dim it.
    const isRoot = depth === 0;

    const wrapperClasses = clsx(
        "node-base relative flex flex-col font-sans border-t-4 transition-all duration-500",
        // Base Score Border
        baseBorderColor,
        // Selection Logic
        isBestPath ? "ring-4 ring-emerald-500/30 shadow-2xl scale-105 z-10" : (!isRoot && "opacity-60 grayscale-[0.6] hover:opacity-100 hover:grayscale-0 hover:scale-105")
    );

    // Add a specialized visual indicator for the selected path
    const SelectionBadge = isBestPath && !isRoot ? (
        <div className="absolute -top-3 -right-3 bg-emerald-500 text-white text-[9px] font-bold px-2 py-1 rounded-full shadow-lg animate-pulse">
            CHOSEN
        </div>
    ) : null;

    // Directive Badges (if this is a structured output node)
    const directive = data.directive;
    const DirectiveInfo = directive ? (
        <div className="mb-2 flex flex-wrap gap-1">
            <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 text-[9px] font-bold uppercase border border-indigo-200">
                {directive.type}
            </span>
            {directive.parameters?.tone && (
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[9px] font-semibold border border-slate-200">
                    {directive.parameters.tone}
                </span>
            )}
        </div>
    ) : null;

    return (
        <div className={wrapperClasses}>
            {SelectionBadge}
            <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-slate-400" isConnectable={isConnectable} />

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                    {type || "Thought"}
                </span>
                <div className={clsx("px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1", scoreColor)}>
                    <div className="w-1.5 h-1.5 rounded-full bg-current" />
                    {localScore?.toFixed(2) ?? "N/A"}
                </div>
            </div>

            {/* Body */}
            <div className="p-4 bg-white relative">
                {/* Subtle highlight background for best path */}
                {isBestPath && <div className="absolute inset-0 bg-emerald-50/30 pointer-events-none" />}
                <div className="relative z-10">
                    {DirectiveInfo}
                    <p className="text-sm font-medium text-slate-700 leading-snug">
                        {label}
                    </p>
                </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-2 bg-slate-50 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-100">
                <span>Path Score</span>
                <span className={clsx("font-mono font-semibold", isBestPath ? "text-emerald-600" : "text-slate-700")}>
                    {pathScore?.toFixed(2) ?? "0.00"}
                </span>
            </div>

            <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-slate-400" isConnectable={isConnectable} />
        </div>
    );
};

export default memo(ThoughtNode);
