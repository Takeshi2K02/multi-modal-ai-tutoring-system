const DynamicVisualContainer = ({ type, data, onMountFailure, onRender }) => {
    useEffect(() => {
        if (!data && onMountFailure) {
            onMountFailure("No data provided to DynamicVisualContainer");
        }
    }, [data, onMountFailure]);

    if (!data) return null;

    const mermaidRef = useRef(null);

    useEffect(() => {
        if (type === 'mermaid' && data && mermaidRef.current) {
            try {
                // Clear state for re-render
                mermaidRef.current.removeAttribute('data-processed');
                // Use run() for explicit rendering in Mermaid 10+
                mermaid.run({
                    nodes: [mermaidRef.current],
                    suppressErrors: true
                }).then(() => {
                    if (onRender) onRender(true);
                }).catch(err => {
                    console.error(">>> [Mermaid] Rendering Failed:", err);
                    if (onRender) onRender(false);
                });
            } catch (err) {
                console.error(">>> [Mermaid] Fatal Error:", err);
                if (onRender) onRender(false);
            }
        }
    }, [type, data, onRender]);

    if (type === 'mermaid') {
        return (
            <div className="my-12 p-8 bg-[#121212]/50 rounded-[40px] border border-white/5 shadow-2xl overflow-hidden group transition-all hover:border-primary/20">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                        <span className="text-[10px] font-black text-primary">VIS</span>
                    </div>
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400">Architectural Schema</h4>
                </div>
                <div className="mermaid flex justify-center" ref={mermaidRef}>
                    {data}
                </div>
            </div>
        );
    }

    if (type === 'table') {
        return (
            <div className="my-8 overflow-x-auto rounded-3xl border border-white/5 bg-black/20 shadow-xl">
                <table className="w-full text-left text-sm text-zinc-400">
                    <thead className="text-[10px] font-black uppercase tracking-widest bg-white/5 text-zinc-500">
                        <tr>
                            {data.headers.map((h, i) => (
                                <th key={i} className="px-6 py-4">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {data.rows.map((row, i) => (
                            <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                                {row.map((cell, j) => (
                                    <td key={j} className="px-6 py-4 font-light">{cell}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    return null;
};

export default DynamicVisualContainer;
