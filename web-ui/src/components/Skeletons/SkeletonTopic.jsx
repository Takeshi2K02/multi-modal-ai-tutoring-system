import React from 'react';

const SkeletonTopic = () => {
    return (
        <div className="flex flex-col lg:flex-row h-full w-full bg-slate-950 overflow-hidden animate-pulse">
            {/* Sidebar Skeleton */}
            <div className="w-full lg:w-80 flex-shrink-0 bg-slate-900/50 border-b lg:border-b-0 lg:border-r border-slate-800 flex flex-col h-auto lg:h-full">
                <div className="p-4 border-b border-slate-800">
                    <div className="h-3 w-20 bg-white/5 rounded-full mb-4" />
                    <div className="h-5 w-48 bg-white/10 rounded-lg mb-4" />
                    <div className="h-2 w-full bg-white/5 rounded-full" />
                </div>
                <div className="p-4 space-y-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="space-y-3">
                            <div className="h-3 w-16 bg-white/5 rounded-full" />
                            <div className="space-y-2 ml-2">
                                <div className="h-8 w-full bg-white/5 rounded-md" />
                                <div className="h-8 w-full bg-white/5 rounded-md" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Area Skeleton */}
            <div className="flex-1 flex flex-col h-full bg-slate-950">
                <div className="h-16 px-8 flex items-center justify-between bg-slate-900/40 border-b border-slate-800">
                    <div className="space-y-2">
                        <div className="h-2 w-16 bg-white/5 rounded-full" />
                        <div className="h-4 w-48 bg-white/10 rounded-lg" />
                    </div>
                    <div className="flex gap-3">
                        <div className="h-10 w-32 bg-white/10 rounded-lg" />
                        <div className="h-10 w-32 bg-white/5 rounded-lg" />
                    </div>
                </div>

                <div className="flex-1 p-8 max-w-5xl mx-auto w-full flex flex-col items-center justify-center">
                    <div className="w-full max-w-2xl space-y-8">
                        <div className="mx-auto w-24 h-24 rounded-full bg-white/5 shadow-xl" />
                        <div className="space-y-4">
                            <div className="h-8 w-3/4 bg-white/10 rounded-lg mx-auto" />
                            <div className="h-8 w-1/2 bg-white/10 rounded-lg mx-auto" />
                        </div>
                        <div className="w-full h-32 bg-white/5 rounded-2xl border border-white/5" />
                        <div className="space-y-4">
                            <div className="w-full h-16 bg-white/5 rounded-xl" />
                            <div className="w-full h-16 bg-white/5 rounded-xl" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SkeletonTopic;
