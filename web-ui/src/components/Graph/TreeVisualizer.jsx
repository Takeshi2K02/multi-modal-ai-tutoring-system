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
        const isSelected = targetNode?.data?.metadata?.pruning_status === 'Selected' || targetNode?.data?.isBestPath;

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
    });

    return { nodes: layoutedNodes, edges: layoutedEdges };
};


const TreeVisualizer = ({ data, onAnimationComplete, progressivePlayback = true }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const nodeTypes = useMemo(() => ({ thoughtNode: ThoughtNode }), []);

    // Progressive Rendering State
    const [fullLayout, setFullLayout] = useState(null);
    const [playbackIndex, setPlaybackIndex] = useState(0);
    const [isPybackComplete, setIsPlaybackComplete] = useState(false);

    // 1. Layout Calculation
    React.useEffect(() => {
        if (data && data.nodes && data.nodes.length > 0) {
            const layouted = getLayoutedElements(data.nodes, data.edges);

            // Only reset playback if it's a completely new synthesis session OR the first node
            const isNewSession = data.nodes.length <= 1;

            if (isNewSession) {
                setNodes([]);
                setEdges([]);
                setPlaybackIndex(0);
                setIsPlaybackComplete(false);
            }

            setFullLayout({ nodes: layouted.nodes, edges: layouted.edges });
        }
    }, [data, setNodes, setEdges]);

    // 2. Playback Loop
    React.useEffect(() => {
        if (!fullLayout || isPybackComplete || !progressivePlayback) return;

        const interval = setInterval(() => {
            setPlaybackIndex((prev) => {
                const nextIndex = prev + 1;
                if (nextIndex >= fullLayout.nodes.length) {
                    // Check if we reached the absolute end of the current known layout
                    // but don't mark as complete if synthesis is still active?
                    // For now, simple length check
                    return prev;
                }
                return nextIndex;
            });
        }, 600); // Faster playback for real-time feel

        return () => clearInterval(interval);
    }, [fullLayout?.nodes?.length, isPybackComplete, progressivePlayback]);

    // Trigger completion callback
    React.useEffect(() => {
        if (isPybackComplete && onAnimationComplete) {
            onAnimationComplete();
        }
    }, [isPybackComplete, onAnimationComplete]);

    // 3. Render Visible Graph based on Index
    React.useEffect(() => {
        if (!fullLayout) return;

        const visibleNodes = progressivePlayback
            ? fullLayout.nodes.slice(0, playbackIndex + 1)
            : fullLayout.nodes;

        const visibleNodeIds = new Set(visibleNodes.map(n => n.id));

        // Connect edges only if both source and target are visible
        const visibleEdges = fullLayout.edges.filter(e =>
            visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
        );

        setNodes(visibleNodes);
        setEdges(visibleEdges);

        // Smooth Fit View on updates
        if (visibleNodes.length > 0) {
            // Project ID: 25-26J-130: Ensure root is visible by adding vertical padding
            fitView({ padding: 0.4, duration: 1000 });
        }

    }, [playbackIndex, fullLayout, setNodes, setEdges, fitView]);

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
