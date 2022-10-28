import React, { FC } from 'react';
import { Text, Tooltip } from '@epam/loveship';
import styles from './status.module.scss';

type StatusProps = {
    color: string;
    statusTitle: string;
    isOverSize?: boolean;
    isTooltip?: boolean;
    placementTooltip?: 'top' | 'bottom' | 'left' | 'right';
};

export const Status: FC<StatusProps> = ({
    statusTitle,
    color,
    isOverSize = false,
    isTooltip = false,
    placementTooltip = 'top'
}) => {
    const overSizeClassName = isOverSize ? styles['status-tag--oversize'] : null;

    const CircleStatus = () => (
        <div
            className={[
                styles['status-tag'],
                overSizeClassName,
                styles[`status-tag--${color}`]
            ].join(' ')}
        />
    );

    return (
        <>
            {isTooltip ? (
                <Tooltip content={statusTitle} placement={placementTooltip}>
                    <CircleStatus />
                </Tooltip>
            ) : (
                <>
                    <CircleStatus />
                    <Text cx={styles.text} fontSize="14">
                        {statusTitle}
                    </Text>
                </>
            )}
        </>
    );
};
