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
    const nodeWidth = 280;
    const nodeHeight = 160;

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

    return { nodes: layoutedNodes, edges };
};


const TreeVisualizer = ({ data }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

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
        <div className="flex-1 h-full bg-gray-50">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-right"
            >
                <Background color="#ccc" gap={20} />
                <Controls />
            </ReactFlow>
        </div>
    );
};

// Wrapper for ReactFlowProvider handled in parent usually, 
// but needed for useReactFlow hook. 
// We'll export a wrapped version or ensure parent has provider.
import { ReactFlowProvider } from 'reactflow';

export default (props) => (
    <ReactFlowProvider>
        <TreeVisualizer {...props} />
    </ReactFlowProvider>
);
