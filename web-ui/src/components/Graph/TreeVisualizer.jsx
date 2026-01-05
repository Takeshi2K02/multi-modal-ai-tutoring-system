import React, { useCallback, useMemo } from 'react';
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


const TreeVisualizer = ({ data }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const nodeTypes = useMemo(() => ({ thoughtNode: ThoughtNode }), []);

    // Effect to update graph when data changes
    React.useEffect(() => {
        if (data && data.nodes && data.edges) {
            const layouted = getLayoutedElements(data.nodes, data.edges);
            setNodes(layouted.nodes);
            setEdges(layouted.edges);

            // Wait for render then fit view
            setTimeout(() => {
                fitView({ padding: 0.2, duration: 800 });
            }, 50);
        }
    }, [data, setNodes, setEdges, fitView]);

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
