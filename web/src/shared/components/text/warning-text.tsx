// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React from 'react';
import { WarningAlert, Text } from '@epam/loveship';
import styles from './warning-text.module.scss';

interface WarningTextProps {
    warningText: string;
    fontsize?: '18' | '10' | '12' | '14' | '16';
}

export const WarningText = ({ warningText, fontsize }: WarningTextProps) => {
    return (
        <WarningAlert cx={styles.wrapper}>
            <Text fontSize={fontsize}>{warningText}</Text>
        </WarningAlert>
    );
};
