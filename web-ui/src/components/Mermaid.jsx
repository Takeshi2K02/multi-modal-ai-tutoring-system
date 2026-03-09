import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const Mermaid = ({ chart }) => {
    const ref = useRef(null);
    const [svg, setSvg] = useState('');
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!chart) return;

        const renderChart = async () => {
            try {
                const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
                // Projects ID: 25-26J-130: Robust line trimming
                const cleanChart = chart
                    .split('\n')
                    .map(line => line.trim())
                    .filter(line => line.length > 0)
                    .join('\n');

                const { svg: generatedSvg } = await mermaid.render(id, cleanChart);
                setSvg(generatedSvg);
                setError(false);
            } catch (err) {
                console.error(">>> [Mermaid Component] Render Error:", err);
                setError(true);
            }
        };

        renderChart();
    }, [chart]);

    if (error) {
        return (
            <div className="p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-xs font-mono">
                [Visual Rendering Error] Please check Mermaid syntax.
            </div>
        );
    }

    return (
        <div
            className="flex justify-center w-full overflow-hidden py-8"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

export default Mermaid;
