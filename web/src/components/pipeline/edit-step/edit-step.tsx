// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import { IconButton } from '@epam/loveship';
import { PipelineTypes, Step } from 'api/typings';
import React, { useState } from 'react';
import { Node, XYPosition } from 'react-flow-renderer';
import { ReactComponent as plusIcon } from '@epam/assets/icons/common/action-add-18.svg';
import { ReactComponent as editIcon } from '@epam/assets/icons/common/action-settings-18.svg';
import { ReactComponent as deleteIcon } from '@epam/assets/icons/common/action-deleteforever-18.svg';
import styles from './edit-step.module.scss';
import { NodeActions } from './node-actions';
import { AddNodeForm } from './add-node-form';
import { EditNodeForm } from './edit-node-form';
import { FlowTransform } from 'react-flow-renderer';

export type EditStepProps = {
    currentElementPosition?: XYPosition;
    availableCategories?: string[];
    step?: Step;
    parentStep?: Step;
    currentNode?: Node;
    node?: Node;
    filterValue?: PipelineTypes;
    parentNode?: Node;
    panoPosition?: FlowTransform;
    readOnly?: boolean;
    addNodeRight: (values: StepValues) => void;
    updateCurrentNode: (values: StepValues) => void;
    onAddStepSuccess: () => void;
    deleteNode: () => void;
};

export type StepValues = {
    model?: string;
    version?: number;
    categories?: string[];
    args?: Record<string, string>;
};

const EditStep = (props: EditStepProps) => {
    const { currentElementPosition, currentNode, readOnly, deleteNode, panoPosition, filterValue } =
        props;

    const [addModal, setAddModal] = useState(false);
    const [editModal, setEditModal] = useState(false);

    const showDelete =
        (!currentNode?.data.step?.steps || currentNode?.data.step?.steps.length === 0) && !readOnly;

    if (!currentElementPosition) return null;
    return (
        <NodeActions position={currentElementPosition} panoPosition={panoPosition}>
            <div>
                <IconButton
                    icon={plusIcon}
                    color="sky"
                    onClick={() => {
                        setEditModal(false);
                        setAddModal(true);
                    }}
                />
                {addModal && (
                    <div className={styles.contextVertical}>
                        <AddNodeForm
                            filterValue={filterValue}
                            parentNode={currentNode}
                            onSave={props.addNodeRight}
                            onSuccess={props.onAddStepSuccess}
                        />
                    </div>
                )}
            </div>
            {!readOnly ? (
                <div>
                    <IconButton
                        icon={editIcon}
                        onClick={() => {
                            setAddModal(false);
                            setEditModal(true);
                        }}
                    />
                    {editModal && (
                        <div className={styles.contextVertical}>
                            <EditNodeForm
                                filterValue={filterValue ?? undefined}
                                parentNode={currentNode?.data.parentNode}
                                node={currentNode}
                                onSave={props.updateCurrentNode}
                                onSuccess={props.onAddStepSuccess}
                            />
                        </div>
                    )}
                </div>
            ) : null}

            {showDelete ? <IconButton icon={deleteIcon} color="sky" onClick={deleteNode} /> : null}
        </NodeActions>
    );
};

export default EditStep;
