import React, { useState } from 'react';
import DraggableResizer from '../DraggableResizer';
import { useTaskAnnotatorContext } from '../../../../../connectors/task-annotator-connector/task-annotator-context';

interface ResizeContainerProps {
    className?: string;
}
const ResizableSyncedContainer: React.FC<ResizeContainerProps> = (props) => {
    const { children, className } = props;
    const [height, setHeight] = useState<number>(300);
    const { SyncedContainer } = useTaskAnnotatorContext();

    return (
        <>
            <SyncedContainer className={className || ''} height={height}>
                {children}
            </SyncedContainer>
            <DraggableResizer onChange={setHeight} currentHeight={height} />
        </>
    );
};

export default ResizableSyncedContainer;
