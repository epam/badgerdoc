import React, { FC, useEffect, useState } from 'react';
import { FlexCell, FlexRow, FlexSpacer, Paginator, Panel, PickerInput } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';

import styles from './table-wrapper.module.scss';
import { pageSizes } from 'shared/primitives';

interface TablePageableProps {
    page: number;
    totalCount: number;
    pageSize: number;
    hasMore?: boolean;
    // need to name more properly
    onPageChange: (page: number, pageSize?: number) => void;
}

export const TableWrapper: FC<TablePageableProps> = ({
    page,
    onPageChange,
    totalCount,
    pageSize,
    hasMore,
    ...props
}) => {
    const [totalPages, setTotalPages] = useState<number>(0);
    const pageSizeDataSource = useArrayDataSource(
        {
            items: Object.values(pageSizes),
            getId: (item) => item
        },
        []
    );

    useEffect(() => {
        setTotalPages(Math.ceil(totalCount / pageSize));
    }, [totalCount]);

    const onTotalPagesChanged = (currentPage: number) => {
        setTotalPages((prevState) => {
            if (prevState === currentPage && hasMore) {
                return prevState + 1;
            }

            return prevState;
        });
    };

    return (
        <Panel cx={styles.container}>
            <div className={styles['pages-container-margin']} />
            {props.children}
            <FlexRow alignItems="center" cx={styles['pages-controls']}>
                <>
                    <FlexSpacer />
                    <Paginator
                        value={page}
                        onValueChange={(newPage) => {
                            onPageChange(newPage);
                            onTotalPagesChanged(newPage);
                        }}
                        totalPages={totalPages}
                        size="24"
                    />
                    <FlexRow cx={styles['page-size-selector']}>
                        <FlexCell minWidth={100}>
                            <span>Show on page</span>
                        </FlexCell>
                        <PickerInput
                            searchPosition="none"
                            minBodyWidth={52}
                            size="24"
                            dataSource={pageSizeDataSource}
                            value={pageSize}
                            onValueChange={(pageSize) => {
                                onPageChange(1, pageSize);
                            }}
                            getName={(item) => String(item)}
                            selectionMode="single"
                            disableClear={true}
                        />
                    </FlexRow>
                </>
            </FlexRow>
        </Panel>
    );
};
