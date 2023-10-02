// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import { PipelineData, Step } from 'api/typings';
import { FlowElement, Node, Position } from 'react-flow-renderer';

export const createFlowElements = (pipeline: PipelineData) => {
    const rootNode = {
        id: 'root',
        targetPosition: Position.Left,
        sourcePosition: Position.Right,
        data: { label: pipeline.name, models: [], categories: [], isPipeline: true },
        style: { backgroundColor: 'lightgray', borderRadius: '20px' },
        position: { x: 50, y: 50 }
    };
    const nodeArr: FlowElement[] = [rootNode];

    const mapSteps = (step: Step, parentNode: Node) => {
        const node: FlowElement = {
            id: step.id || '',
            targetPosition: Position.Left,
            sourcePosition: Position.Right,
            data: {
                label: step.model,
                models: [...parentNode.data.models, step.model],
                categories: step.categories ?? [],
                step,
                parentNode
            },
            position: { x: 50, y: 50 }
        };
        nodeArr.push(node, {
            id: `smoothstep-${parentNode.id}-${step.id}`,
            source: parentNode.id,
            type: 'smoothstep',
            target: (step.id || '').toString(),
            label: node.data.categories.join(', ')
        });
        if (!step?.steps?.length) {
            return;
        }
        step.steps.forEach((child) => mapSteps(child, node));
    };
    pipeline.steps?.forEach((step) => mapSteps(step, rootNode));
    return nodeArr;
};
