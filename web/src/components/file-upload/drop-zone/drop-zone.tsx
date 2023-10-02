// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useCallback, useState } from 'react';
import { DropSpotRenderParams, Panel } from '@epam/loveship';

import styles from './drop-zone.module.scss';

enum DragState {
    ENTER = 'hover',
    LEAVE = ''
}

export const DropZone: FC<DropSpotRenderParams['eventHandlers']> = ({
    onDrop,
    onDragEnter,
    onDragLeave,
    onDragOver,
    children
}) => {
    const [dragState, changeDragState] = useState<DragState>(DragState.LEAVE);

    const onDropZoneEnter = useCallback((event) => {
        changeDragState(DragState.ENTER);
        onDragEnter(event);
    }, []);

    const onDropZoneDrop = useCallback((event) => {
        changeDragState(DragState.LEAVE);
        onDrop(event);
    }, []);

    const onDropZoneLeave = useCallback((event) => {
        changeDragState(DragState.LEAVE);
        onDragLeave(event);
    }, []);
    return (
        <section
            className={`flex flex-cell ${styles['drop-zone-wrapper']} ${styles.section}`}
            onDrop={onDropZoneDrop}
            onDragEnter={onDropZoneEnter}
            onDragLeave={onDropZoneLeave}
            onDragOver={onDragOver}
        >
            <Panel
                cx={[
                    styles['drop-zone'],
                    { [styles['drop-zone--hover']]: dragState === DragState.ENTER },
                    ' flex-cell flex-center justify-stretch align-stretch'
                ]}
            >
                {children}
            </Panel>
        </section>
    );
};
