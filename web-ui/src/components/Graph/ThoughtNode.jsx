import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import clsx from 'clsx';

const ThoughtNode = ({ data, isConnectable }) => {
    const { label, localScore, pathScore, type } = data;

    const scoreColor = localScore >= 0.8 ? 'text-emerald-600 bg-emerald-50'
        : localScore >= 0.5 ? 'text-amber-600 bg-amber-50'
            : 'text-rose-600 bg-rose-50';

    const borderColor = localScore >= 0.8 ? 'border-t-emerald-500'
        : localScore >= 0.5 ? 'border-t-amber-500'
            : 'border-t-rose-500';

    return (
        <div className={clsx("node-base relative flex flex-col font-sans border-t-4", borderColor)}>
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
            <div className="p-4 bg-white">
                <p className="text-sm font-medium text-slate-700 leading-snug">
                    {label}
                </p>
            </div>

            {/* Footer */}
            <div className="px-4 py-2 bg-slate-50 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-100">
                <span>Path Score</span>
                <span className="font-mono font-semibold text-slate-700">{pathScore?.toFixed(2) ?? "0.00"}</span>
            </div>

            <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-slate-400" isConnectable={isConnectable} />
        </div>
    );
};

export default memo(ThoughtNode);
