import React, { useRef, useState } from 'react';

interface DraggableResizerProps {
    onChange: (heightDiff: number) => void;
    currentHeight: number;
}

const DraggableResizer: React.FC<DraggableResizerProps> = ({ onChange, currentHeight }) => {
    const [initialDiff, setInitialDiff] = useState<number>(0);
    const ref = useRef<HTMLDivElement>(null);

    const onDrag = (newHeight: number) => {
        if (newHeight) {
            onChange(newHeight - initialDiff);
        }
    };

    return (
        <div
            ref={ref}
            style={{ height: '24px', cursor: 'row-resize' }}
            draggable
            onDrag={(e) => onDrag(e.pageY)}
            onDragStart={(e) => {
                setInitialDiff(e.pageY - currentHeight);
            }}
        >
            <div style={{ background: '#FFF', height: '2px' }} />
        </div>
    );
};

export default DraggableResizer;
