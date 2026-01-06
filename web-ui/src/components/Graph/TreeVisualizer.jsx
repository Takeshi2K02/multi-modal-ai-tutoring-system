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

    // Set node size (width 256px + padding, height approx 150px)
    // Set node size (width 350px + padding, height approx 200px)
    const nodeWidth = 400; // Increased to allow spacing
    const nodeHeight = 220; // Increased height

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

    const layoutedEdges = edges.map((edge) => ({
        ...edge,
        type: 'smoothstep',
        animated: true,
        style: {
            stroke: '#64748b', // Slate-500
            strokeWidth: 3
        }
    }));

    return { nodes: layoutedNodes, edges: layoutedEdges };
};


const TreeVisualizer = ({ data, onAnimationComplete }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const nodeTypes = useMemo(() => ({ thoughtNode: ThoughtNode }), []);

    // Progressive Rendering State
    const [fullLayout, setFullLayout] = useState(null);
    const [playbackIndex, setPlaybackIndex] = useState(0);
    const [isPybackComplete, setIsPlaybackComplete] = useState(false);

    // 1. Initial Layout Calculation (Runs once when data arrives)
    React.useEffect(() => {
        if (data && data.nodes && data.edges) {
            const layouted = getLayoutedElements(data.nodes, data.edges);

            // Sort nodes by rank/depth visually (Top-Down BFS roughly based on Y position)
            // This ensures they appear top-to-bottom, "thinking" step by step.
            const sortedNodes = [...layouted.nodes].sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x);

            setFullLayout({ nodes: sortedNodes, edges: layouted.edges });
            setPlaybackIndex(0);
            setIsPlaybackComplete(false);
            setNodes([]); // Start empty
            setEdges([]);
        }
    }, [data, setNodes, setEdges]); // Removed fitView dependency to avoid loops

    // 2. Playback Loop
    React.useEffect(() => {
        if (!fullLayout || isPybackComplete) return;

        const interval = setInterval(() => {
            setPlaybackIndex((prev) => {
                const nextIndex = prev + 1;

                // Check if done
                if (nextIndex >= fullLayout.nodes.length) {
                    setIsPlaybackComplete(true);
                    return prev; // Stop incrementing
                }
                return nextIndex;
            });
        }, 800); // 800ms per node "thought"

        return () => clearInterval(interval);
    }, [fullLayout, isPybackComplete]);

    // Trigger completion callback
    React.useEffect(() => {
        if (isPybackComplete && onAnimationComplete) {
            onAnimationComplete();
        }
    }, [isPybackComplete, onAnimationComplete]);

    // 3. Render Visible Graph based on Index
    React.useEffect(() => {
        if (!fullLayout) return;

        const visibleNodes = fullLayout.nodes.slice(0, playbackIndex + 1);
        const visibleNodeIds = new Set(visibleNodes.map(n => n.id));

        // Connect edges only if both source and target are visible
        const visibleEdges = fullLayout.edges.filter(e =>
            visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
        );

        setNodes(visibleNodes);
        setEdges(visibleEdges);

        // Smooth Fit View on updates
        if (visibleNodes.length > 0) {
            fitView({ padding: 0.2, duration: 500 }); // Smooth pan
        }

    }, [playbackIndex, fullLayout, setNodes, setEdges, fitView]);

    return (
        <div className="flex-1 h-full bg-slate-950">
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
                <Background color="#1e293b" gap={20} />
                <Controls className="bg-white/10 border-white/20 fill-slate-300 text-slate-300" />
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
