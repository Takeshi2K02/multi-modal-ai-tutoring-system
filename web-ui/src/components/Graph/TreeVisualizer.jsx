import React, { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    addEdge,
    useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import ThoughtNode from './ThoughtNode';

const nodeTypes = { thoughtNode: ThoughtNode };

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Set node size (width 300px + padding, height approx 250px)
    const nodeWidth = 400;
    const nodeHeight = 350;

    dagreGraph.setGraph({ rankdir: direction });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        node.targetPosition = 'top';
        node.sourcePosition = 'bottom';

        // Shift slightly so it's centered
        node.position = {
            x: nodeWithPosition.x - nodeWidth / 2,
            y: nodeWithPosition.y - nodeHeight / 2,
        };

        return node;
    });

    const layoutedEdges = edges.map((edge) => {
        const targetNode = nodes.find(n => n.id === edge.target);
        const sourceNode = nodes.find(n => n.id === edge.source);
        const isSelected = targetNode?.data?.metadata?.pruning_status === 'Selected' || targetNode?.data?.isBestPath;

        // PROJECT ID: 25-26J-130: Drop edge if source or target doesn't exist in the current layout
        if (!sourceNode || !targetNode) return null;

        return {
            ...edge,
            type: 'smoothstep',
            animated: !isSelected,
            style: {
                stroke: isSelected ? '#00f2ff' : '#6366F1', // Project ID: 25-26J-130: Vibrant Green/Cyan highlight
                strokeWidth: isSelected ? 6 : 3,
                filter: isSelected ? 'drop-shadow(0 0 12px rgba(0, 242, 255, 0.8))' : 'none'
            }
        };
    }).filter(Boolean); // PROJECT ID: 25-26J-130: Clean up null edges

    return { nodes: layoutedNodes, edges: layoutedEdges };
};


const TreeVisualizer = ({ data, onAnimationComplete, progressivePlayback = true, isComplete = false }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const [visibleLayout, setVisibleLayout] = useState(null);
    const [playbackIndex, setPlaybackIndex] = useState(0);
    const [isPybackComplete, setIsPlaybackComplete] = useState(false);
    const layoutRef = React.useRef({ nodes: [], edges: [] });

    // 1. Layout Calculation & Buffer Sync
    React.useEffect(() => {
        if (data && data.nodes && data.nodes.length > 0) {
            const layouted = getLayoutedElements(data.nodes, data.edges);

            // PROJECT ID: 25-26J-130: Reset logic for new sessions
            const isNewSession = data.nodes.length <= 1;
            if (isNewSession) {
                setPlaybackIndex(0);
                setIsPlaybackComplete(false);
            }

            layoutRef.current = layouted;
            setVisibleLayout(layouted); // Force redraw if already complete
        }
    }, [data.nodes.length]); // Only re-layout when structural changes happen

    // 2. Stable Playback Interval (Decoupled from data arrival)
    React.useEffect(() => {
        if (!progressivePlayback || isPybackComplete) return;

        const interval = setInterval(() => {
            setPlaybackIndex((prev) => {
                const totalAvailable = layoutRef.current?.nodes?.length || 0;
                if (prev + 1 < totalAvailable) {
                    return prev + 1;
                }

                // If we've reached the end of discovered nodes but synthesis is done, mark as complete
                if (isComplete && prev + 1 >= totalAvailable) {
                    setIsPlaybackComplete(true);
                }
                return prev;
            });
        }, 850); // Direct requirement: deliberate node-by-node stream

        return () => clearInterval(interval);
    }, [progressivePlayback, isPybackComplete, isComplete]);

    // Trigger completion callback
    React.useEffect(() => {
        if (isPybackComplete && onAnimationComplete) {
            onAnimationComplete();
        }
    }, [isPybackComplete, onAnimationComplete]);

    // 3. Selective Visibility Engine
    React.useEffect(() => {
        const fullLayout = layoutRef.current;
        if (!fullLayout?.nodes?.length) return;

        const visibleNodes = progressivePlayback
            ? fullLayout.nodes.slice(0, playbackIndex + 1)
            : fullLayout.nodes;

        const visibleNodeIds = new Set(visibleNodes.map(n => n.id));

        const visibleEdges = fullLayout.edges.filter(e =>
            visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
        );

        setNodes(visibleNodes);
        setEdges(visibleEdges);
    }, [playbackIndex, visibleLayout, progressivePlayback, setNodes, setEdges]);

    return (
        <div className="flex-1 h-full bg-edu-bg-light dark:bg-edu-bg-dark transition-colors relative z-[100]">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-right"
                nodesDraggable={false} // Keep layout stable during playback
            >
                <Background color="#6366F1" opacity={0.05} gap={20} />
                <Controls className="bg-edu-surface-light dark:bg-white/10 border-edu-border-light dark:border-white/20 fill-edu-text-light dark:fill-slate-300 text-edu-text-light dark:text-slate-300" />
            </ReactFlow>
        </div>
    );
};

// Wrapper for ReactFlowProvider handled in parent usually, 
// but needed for useReactFlow hook. 
import { ReactFlowProvider } from 'reactflow';

export default function WrappedTreeVisualizer(props) {
    return (
        <ReactFlowProvider>
            <TreeVisualizer {...props} />
        </ReactFlowProvider>
    );
}
