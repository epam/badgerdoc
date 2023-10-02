// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { FC } from 'react';
import { JobStatus } from 'api/typings/jobs';
import { Text, Tooltip } from '@epam/loveship';
import styles from './status.module.scss';

type StatusProps = {
    color: string;
    statusTitle: JobStatus | string;
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
