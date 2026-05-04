import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

// Recognized opening keywords for a valid Mermaid diagram
const VALID_DECLARATIONS = [
    'graph', 'flowchart', 'sequencediagram', 'classdiagram',
    'erdiagram', 'statediagram', 'gantt', 'pie', 'gitgraph'
];

// Module-level counter — incremented once per component mount via useRef.
// Gives each instance a stable, collision-free ID that never changes across re-renders.
let _diagramSeq = 0;

/**
 * Sanitize a raw Mermaid string before handing it to the renderer.
 * Returns the cleaned string, or null if the diagram is unrecoverable.
 */
function sanitizeMermaid(raw) {
    if (!raw || typeof raw !== 'string') return null;

    let text = raw.trim();

    // 1. Strip markdown code fences: ```mermaid ... ``` or ``` ... ```
    text = text.replace(/^```(?:mermaid)?\s*\n?/i, '').replace(/\n?```\s*$/i, '').trim();

    // 2. Strip leading ** bold markers
    text = text.replace(/^\*\*+/, '').trim();

    // 3. Remove invisible / zero-width Unicode that silently breaks the parser
    text = text
        .replace(/[​‌‍﻿­]/g, '')  // zero-width + soft hyphen
        .replace(/ /g, ' ')                             // non-breaking space → regular space
        .replace(/[“”]/g, '"')                    // typographic double quotes
        .replace(/[‘’]/g, "'")                    // typographic single quotes
        .replace(/[–—]/g, '-');                   // en/em dash → hyphen

    // 4. Fix nested square brackets in node labels: [text [inner]] -> [text (inner)]
    // Using user-requested regex: \[([^\]]*)\[([^\]]*)\]([^\]]*)\]
    text = text.replace(/\[([^\]]*)\[([^\]]*)\]([^\]]*)\]/g, '[$1($2)$3]');

    // 5. Trim and filter blank lines
    text = text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .join('\n');

    if (!text) return null;

    // 6. Validate: first token must be a recognized Mermaid graph declaration
    const firstToken = text.split(/[\s({[]/)[0].toLowerCase();
    const isValid = VALID_DECLARATIONS.some(decl => firstToken.startsWith(decl));
    if (!isValid) return null;

    return text;
}

const Mermaid = ({ chart }) => {
    const [svg, setSvg] = useState('');
    const [error, setError] = useState(null);   // null | { message: string, rawChart: string }
    const [loading, setLoading] = useState(false);

    // Stable ID for this instance — assigned once at mount, never recomputed
    const diagramId = useRef(`mermaid-diagram-${++_diagramSeq}`);

    useEffect(() => {
        if (!chart) return;

        let cancelled = false;

        const render = async () => {
            setLoading(true);
            setError(null);
            setSvg('');

            // Re-initialize with safe, locked config on every render call.
            // suppressErrors prevents Mermaid from injecting its own error popup into the DOM.
            mermaid.initialize({
                startOnLoad: false,
                theme: 'dark',
                securityLevel: 'loose',
                fontFamily: 'Inter, system-ui, sans-serif',
                suppressErrors: true,
            });

            const sanitized = sanitizeMermaid(chart);
            if (!sanitized) {
                if (!cancelled) {
                    console.error(
                        '[Mermaid Parse Error] Chart rejected during sanitization — no valid declaration found.\nRaw input:\n',
                        chart
                    );
                    setError({ message: 'No valid Mermaid graph declaration found after sanitization.', rawChart: chart });
                    setLoading(false);
                }
                return;
            }

            // Remove any stale DOM artifact from a previous render with this ID
            // to prevent "Element with id already exists" errors on prop updates.
            const stale = document.getElementById(diagramId.current);
            if (stale) stale.remove();

            try {
                const { svg: generatedSvg } = await mermaid.render(diagramId.current, sanitized);
                if (!cancelled) {
                    setSvg(generatedSvg);
                    setLoading(false);
                }
            } catch (err) {
                if (!cancelled) {
                    console.error(
                        '[Mermaid Parse Error]', err?.message ?? String(err),
                        '\n\nSanitized chart passed to renderer:\n', sanitized
                    );
                    setError({ message: err?.message ?? String(err), rawChart: chart });
                    setLoading(false);
                }
            }
        };

        render();
        return () => { cancelled = true; };
    }, [chart]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="flex items-center gap-3 text-zinc-500">
                    <div className="w-4 h-4 border-2 border-primary/40 border-t-primary rounded-full animate-spin" />
                    <span className="text-xs font-mono tracking-wider">Rendering diagram...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 border-b border-amber-500/20 bg-amber-500/10">
                    <span className="text-[10px] font-black uppercase tracking-widest text-amber-400">
                        Diagram Source
                    </span>
                    <span className="text-[10px] text-amber-400/60">— render failed, showing raw</span>
                </div>
                <pre className="p-4 text-xs font-mono text-amber-300/80 whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-64 overflow-y-auto">
                    {error.rawChart}
                </pre>
            </div>
        );
    }

    if (!svg) return null;

    return (
        <div
            className="flex justify-center w-full overflow-hidden py-8"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

export default Mermaid;
