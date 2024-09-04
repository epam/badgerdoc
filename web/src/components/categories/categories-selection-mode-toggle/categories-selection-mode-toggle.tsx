import { FlexCell, RadioGroup } from '@epam/loveship';
import React from 'react';
import './categories-selection-mode-toggle.scss';
import {
    AnnotationBoundMode,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType
} from '../../../shared';
import { FileMetaInfo } from '../../../pages/document/document-page-sidebar-content/document-page-sidebar-content';

type SelectionModeSelectorProps = {
    selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType;
    selectionMode: AnnotationBoundMode;
    onChangeSelectionType: (
        newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
    ) => void;
    fileMetaInfo: FileMetaInfo;
    selectedTool: AnnotationImageToolType;
    onChangeSelectedTool: (newTool: AnnotationImageToolType) => void;
    isDisabled?: boolean;
};

export const CategoriesSelectionModeToggle: React.FC<SelectionModeSelectorProps> = ({
    selectionType,
    selectionMode,
    onChangeSelectionType,
    fileMetaInfo,
    selectedTool,
    onChangeSelectedTool,
    isDisabled = false
}: SelectionModeSelectorProps) => {
    const regularSelectionTypes = [
        { id: 'box', name: 'box' },
        { id: 'text', name: 'text' },
        { id: 'free-box', name: 'free-box' },
        { id: 'table', name: 'table' },
        { id: 'document', name: 'document' }
    ];
    const linksSelectionTypes = [
        { id: 'Chain', name: 'Chain' },
        { id: 'All to all', name: 'All to all' }
    ];
    const picSelectionTypes = [
        { id: 'free-box', name: 'free-box' },
        { id: 'box', name: 'box' },
        { id: 'text', name: 'text' },
        { id: 'table', name: 'table' },
        { id: 'document', name: 'document' }
    ];

    const getSelectionType = () => {
        if (fileMetaInfo.extension === '.jpg') {
            return picSelectionTypes;
        }

        if (selectionMode === 'link') return linksSelectionTypes;
        return regularSelectionTypes;
    };

    const getSelectionLabel = () => {
        if (fileMetaInfo.extension === '.jpg') {
            return 'Annotation type';
        }

        if (selectionMode === 'link') return 'Links type';
        return 'Annotation type';
    };
    return (
        <div className="selection-mode-wrapper">
            <div className="selection-mode-title">{`${getSelectionLabel()}`}</div>
            <FlexCell>
                {selectionMode === 'segmentation' ? (
                    <RadioGroup
                        //TODO: Be aware that line below is the correct form of what we're trying to achieve
                        // Just for now - we need to implement all tools first then we can uncomment this
                        //items={toolNames.map((el) => ({ id: el, name: el }))}
                        items={[
                            { id: 'pen', name: 'pen' },
                            { id: 'brush', name: 'brush' },
                            { id: 'select', name: 'select' },
                            { id: 'eraser', name: 'eraser' },
                            { id: 'wand', name: 'wand' }
                        ]}
                        value={selectedTool}
                        onValueChange={onChangeSelectedTool}
                        direction="horizontal"
                        cx="selection-mode-toggle"
                        isDisabled={isDisabled}
                    />
                ) : (
                    <RadioGroup
                        items={getSelectionType()}
                        value={selectionType}
                        onValueChange={onChangeSelectionType}
                        direction="horizontal"
                        cx="selection-mode-toggle"
                        isDisabled={isDisabled}
                    />
                )}
            </FlexCell>
        </div>
    );
};
