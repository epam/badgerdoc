import React, { FC } from 'react';
import { Button, FlexRow, FlexSpacer, Panel } from '@epam/loveship';

import styles from './table-filter-wrapper.module.scss';

interface TableFilterWrapperProps {
    onApply: () => void;
    onReset: () => void;
    children: any;
}

export const TableFilterWrapper: FC<TableFilterWrapperProps> = ({ children, onApply, onReset }) => {
    return (
        <Panel shadow={true} cx={styles['table-filter-wrapper']}>
            <FlexRow>{children}</FlexRow>
            <FlexRow>
                <FlexSpacer></FlexSpacer>
                <Button
                    color="sky"
                    caption="Reset"
                    size="24"
                    fill="light"
                    onClick={onReset}
                ></Button>
                <Button color="sky" caption="Apply" size="24" onClick={onApply}></Button>
            </FlexRow>
        </Panel>
    );
};
