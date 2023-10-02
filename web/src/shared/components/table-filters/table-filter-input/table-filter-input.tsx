// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useCallback, useState, FC } from 'react';
import { IEditable } from '@epam/uui';
import { FlexRow, NumericInput, Panel } from '@epam/loveship';

import { TableFilterWrapper } from '../table-filter-wrapper/table-filter-wrapper';

interface TableFilterWrapperProps extends IEditable<number> {}

export const TableFilterInput: FC<TableFilterWrapperProps> = ({ onValueChange, value }) => {
    const [filterValue, setFilterValue] = useState<number>(value ?? 0);
    const onApply = useCallback(() => {
        onValueChange(filterValue);
    }, [filterValue, onValueChange]);

    const onInputValueChange = useCallback(
        (value: number) => {
            setFilterValue(value);
        },
        [setFilterValue]
    );

    const onReset = useCallback(() => {
        setFilterValue(0);
        onValueChange(0);
    }, [setFilterValue, onValueChange]);

    return (
        <TableFilterWrapper onApply={onApply} onReset={onReset}>
            <Panel>
                <FlexRow>Show files that have size more than: {filterValue} bytes</FlexRow>
                <FlexRow>
                    <NumericInput
                        min={0}
                        max={Number.MAX_SAFE_INTEGER}
                        value={filterValue}
                        onValueChange={onInputValueChange}
                    ></NumericInput>
                </FlexRow>
            </Panel>
        </TableFilterWrapper>
    );
};
