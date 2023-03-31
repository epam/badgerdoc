import React, { useEffect, useRef, useState } from 'react';
import DraggableResizer from '../DraggableResizer';
import { useTaskAnnotatorContext } from '../../../../../connectors/task-annotator-connector/task-annotator-context';
import { GridVariants } from 'shared/constants/task';

interface ResizeContainerProps {
    className?: string;
    rowsCount: number;
    type?: GridVariants;
}

const ResizableSyncedContainer: React.FC<ResizeContainerProps> = ({
    children,
    className,
    rowsCount,
    type = GridVariants.horizontal
}) => {
    const ref = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState<number>(300);
    const [height, setHeight] = useState<number>(300);
    const { SyncedContainer } = useTaskAnnotatorContext();

    useEffect(() => {
        if (!ref.current) return;
        setWidth(ref.current?.getBoundingClientRect().width / rowsCount);
    }, []);

    return (
        <>
            <SyncedContainer
                className={className}
                width={type === GridVariants.vertical ? width : undefined}
                height={type === GridVariants.horizontal ? height : undefined}
            >
                <div ref={ref}>{children}</div>
            </SyncedContainer>
            <DraggableResizer
                type={type}
                currentWidth={width}
                currentHeight={height}
                onChange={type === GridVariants.horizontal ? setHeight : setWidth}
            />
        </>
    );
};

export default ResizableSyncedContainer;
