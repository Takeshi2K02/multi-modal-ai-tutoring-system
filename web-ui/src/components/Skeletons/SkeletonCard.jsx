import React from 'react';

const SkeletonCard = () => {
    return (
        <div className="bg-white/5 backdrop-blur-3xl border border-white/10 rounded-3xl p-6 h-[220px] flex flex-col justify-between animate-pulse">
            <div>
                <div className="flex items-center justify-between mb-4">
                    <div className="h-4 w-24 bg-white/10 rounded-full" />
                    <div className="h-6 w-6 bg-white/10 rounded-full" />
                </div>
                <div className="space-y-3">
                    <div className="h-6 w-full bg-white/10 rounded-lg" />
                    <div className="h-6 w-3/4 bg-white/10 rounded-lg" />
                </div>
            </div>

            <div className="space-y-4">
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-white/10 w-1/3 rounded-full" />
                </div>
                <div className="flex items-center justify-between">
                    <div className="h-10 w-32 bg-white/10 rounded-full" />
                    <div className="h-4 w-12 bg-white/10 rounded-full" />
                </div>
            </div>
        </div>
    );
};

export default SkeletonCard;
