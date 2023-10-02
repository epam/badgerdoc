// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import { Category, Step } from 'api/typings';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Elements, FlowElement, FlowTransform, isNode, Node } from 'react-flow-renderer';
import { EditStepProps, StepValues } from '../edit-step/edit-step';
import { v4 as uuidv4 } from 'uuid';

type UsePipelineEditorResult = {
    flowProps: {
        onNodeDrag?: (event: React.MouseEvent, node: Node) => void;
        onNodeDragStop?: (event: React.MouseEvent, node: Node) => void;
        onSelectionChange?: (elements: Elements | null) => void;
        onMove?: (event?: FlowTransform) => void;
        onMoveStart?: (event?: FlowTransform) => void;
        onMoveEnd?: (event?: FlowTransform) => void;
    };
    editStepProps: EditStepProps;
    showAdd: boolean;
    allCategories?: Category[];
};

export const usePipelineEditor = (
    flowElements: FlowElement[],
    onAddStep?: (newStep: Step, parentStepId?: string) => void,
    onUpdateStep?: (step: Step) => void,
    onDeleteStep?: (deleteStep: Step, parentStepId?: string) => void
): UsePipelineEditorResult => {
    const [currentNodeId, setCurrentNodeId] = useState<string | undefined>(undefined);
    const [showAdd, setShowAdd] = useState(false);
    const [currentNodePosition, setCurrentNodePosition] = useState({ x: 0, y: 0 });
    const [panoPosition, setPanoPositions] = useState<FlowTransform>({ x: 0, y: 0, zoom: 1 });

    const currentNode: Node | undefined = useMemo(() => {
        if (!currentNodeId) return;
        const element = flowElements.find((element) => element.id === currentNodeId);
        if (element && isNode(element)) {
            return element;
        }
    }, [currentNodeId]);

    const isPipeline = currentNode?.data.isPipeline;

    const addNodeRight = useCallback(
        (values: StepValues) => {
            const newStep: Step = {
                ...values,
                id: uuidv4(),
                model: values.model!,
                version: values.version!,
                model_url: values.model!,
                categories: values.categories!,
                args: values.args!
            };
            const parentStepId = !isPipeline ? currentNodeId : undefined;
            onAddStep?.(newStep, parentStepId);
        },
        [currentNodeId, onAddStep, isPipeline]
    );

    const deleteNode = useCallback(() => {
        const parentNode = currentNode?.data.parentNode;
        const parentStepId = !parentNode.data.isPipeline ? parentNode.id : undefined;
        onDeleteStep?.(currentNode?.data.step, parentStepId);
    }, [currentNode, onDeleteStep, isPipeline]);

    const updateCurrentNode = useCallback(
        (values: StepValues) => {
            onUpdateStep?.({
                ...currentNode?.data?.step,
                model: values.model!,
                version: values.version!,
                model_url: values.model!,
                categories: values.categories!,
                args: values.args!
            });
        },
        [currentNode, onUpdateStep]
    );

    const onAddStepSuccess = () => {
        setShowAdd(false);
        setCurrentNodeId(undefined);
    };

    useEffect(() => {
        setShowAdd(false);
    }, [flowElements]);

    return {
        flowProps: {
            onNodeDrag: (e, node) => {
                setCurrentNodePosition({
                    x: node.position.x + panoPosition.x,
                    y: node.position.y + panoPosition.y
                });
            },
            onNodeDragStop: (e, node) => {
                setCurrentNodePosition({
                    x: node.position.x + panoPosition.x,
                    y: node.position.y + panoPosition.y
                });
            },
            onSelectionChange: (elements) => {
                const node = elements?.length === 1 && isNode(elements[0]) ? elements[0] : null;
                if (node && flowElements.some(({ id }) => id === node.id)) {
                    setShowAdd(true);
                    setCurrentNodePosition({
                        x: node.position.x,
                        y: node.position.y
                    });
                    setCurrentNodeId(node.id);
                } else {
                    setShowAdd(false);
                }
            },
            onMoveStart: (e: FlowTransform | undefined) => {
                e && setPanoPositions(e);
            },
            onMove: (e: FlowTransform | undefined) => {
                e && setPanoPositions(e);
            },
            onMoveEnd: (e: FlowTransform | undefined) => {
                e && setPanoPositions(e);
            }
        },
        editStepProps: {
            currentElementPosition: currentNodePosition,
            availableCategories: [],
            step: currentNode?.data?.step,
            currentNode,
            readOnly: isPipeline,
            panoPosition: panoPosition,
            addNodeRight,
            updateCurrentNode,
            onAddStepSuccess: onAddStepSuccess,
            deleteNode
        },
        showAdd
    };
};
