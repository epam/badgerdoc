// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { XYPosition } from 'react-flow-renderer';
import styles from './edit-step.module.scss';

export const NodeActions: FC<{
    position: XYPosition;
    panoPosition?: { x: number; y: number; zoom: number };
}> = ({ position, panoPosition, children }) => {
    return (
        <div
            style={{
                transform: `translate(${panoPosition?.x}px, ${panoPosition?.y}px) scale(${panoPosition?.zoom})`,
                transformOrigin: '0 0',
                position: 'absolute',
                top: 0,
                left: 0,
                zIndex: 5
            }}
        >
            <div
                style={{
                    top: `${position.y - 10}px`,
                    left: `${position.x + 158}px`
                }}
                className={styles.rightButton}
            >
                {children}
            </div>
        </div>
    );
};
