// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import { cx } from '@epam/uui-core';
import React, { DragEvent, useState } from 'react';
import { GridVariants } from 'shared/constants/task';
import styles from './styles.module.scss';

interface DraggableResizerProps {
    currentHeight: number;
    currentWidth?: number;
    type?: GridVariants;
    onChange: (heightDiff: number) => void;
}

const DraggableResizer: React.FC<DraggableResizerProps> = ({
    type = GridVariants.horizontal,
    onChange,
    currentWidth = 0,
    currentHeight = 0
}) => {
    const [initialDiff, setInitialDiff] = useState<number>(0);

    const isVertical = type === GridVariants.vertical;
    const isHorizontal = type === GridVariants.horizontal;

    const handleDrag = ({ pageY, pageX }: DragEvent<HTMLDivElement>) => {
        if (isHorizontal && pageY) {
            onChange(pageY - initialDiff);
        }
        if (isVertical && pageX) {
            onChange(pageX - initialDiff);
        }
    };

    const handleDragStart = ({ pageY, pageX }: DragEvent<HTMLDivElement>) => {
        if (isHorizontal) {
            setInitialDiff(pageY - currentHeight);
        }
        if (isVertical) {
            setInitialDiff(pageX - currentWidth);
        }
    };

    const containerClassName = cx({
        [styles.vertical]: isVertical,
        [styles.horizontal]: isHorizontal
    });
    const innerClassName = cx({
        [styles['vertical__inner']]: isVertical,
        [styles['horizontal__inner']]: isHorizontal
    });

    return (
        <div
            draggable
            onDrag={handleDrag}
            onDragStart={handleDragStart}
            className={containerClassName}
        >
            <div className={innerClassName} />
        </div>
    );
};

export default DraggableResizer;
