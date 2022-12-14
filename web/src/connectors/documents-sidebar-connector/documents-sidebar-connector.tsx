import React, { useEffect, useState } from 'react';
import { FlexRow, FlexSpacer, LinkButton, SearchInput, VirtualList } from '@epam/loveship';
import noop from 'lodash/noop';
import styles from './documents-sidebar-connector.module.scss';

import {
    Filter,
    PagedResponse,
    QueryHookParamsType,
    QueryHookType,
    SortingDirection
} from 'api/typings';
import { VirtualListState } from '@epam/uui';
import { pageSizes } from 'shared/primitives';

type DocumentsSidebarConnectorProps<T> = {
    title: string;
    resetCaption?: string;
    activeEntity?: T | null;
    useEntitiesHook: QueryHookType<QueryHookParamsType<T>, PagedResponse<T>>;
    onReset?: () => void;
    rowRender: (entity: T) => React.ReactNode;
    renderCreateBtn?: RenderCreateBtn;
    sortField: keyof T;
    filters?: Array<Filter<keyof T>>;
};
export type RenderCreateBtn = (params: { onCreated: () => void }) => React.ReactNode;

const size = pageSizes._100;

export const DocumentsSidebarConnector = <T extends object>({
    title,
    resetCaption,
    activeEntity = null,
    useEntitiesHook,
    rowRender,
    onReset = noop,
    renderCreateBtn = () => null,
    sortField,
    filters
}: DocumentsSidebarConnectorProps<T>) => {
    const [searchText, setSearchText] = useState('');
    const [page, setPageNum] = useState(1);
    const [items, setItems] = useState<T[]>([]);
    const [canLoad, setCanLoad] = useState(false);

    const sortConfig = {
        field: sortField,
        direction: SortingDirection.ASC
    };
    const { data } = useEntitiesHook({ searchText, sortConfig, page, size, filters }, {});

    useEffect(() => {
        setPageNum(1);
    }, [searchText, sortConfig]);

    useEffect(() => {
        if (data?.data !== undefined) {
            setItems((state) => [...(page > 1 ? state : []), ...data.data]);
            setCanLoad(data?.data.length === size);
        }
    }, [data?.data]);

    const [listState, setListState] = useState<VirtualListState>({});
    const { topIndex = 0, visibleCount = 10 } = listState;

    const visibleItems = items.slice(topIndex, topIndex + visibleCount);

    const visibleRows = visibleItems.map((item) => rowRender(item));

    const onSearchChange = (text: string) => {
        setSearchText(text);
    };

    const handleScroll = (clientHeight: number, scrollHeight: number, scrollTop: number) => {
        if (canLoad && scrollHeight - clientHeight - scrollTop <= clientHeight / 2) {
            setCanLoad(false);
            setPageNum(page + 1);
        }
    };

    const handleEntityCreated = () => {
        setPageNum(1);
    };

    return (
        <div className={styles['sidebar']}>
            <FlexRow padding="18" alignItems="center">
                <div className="flex align-vert-center m-t-20">
                    <h2 className="m-0">{title}</h2>
                </div>
                <FlexSpacer />
            </FlexRow>
            <SearchInput
                cx={styles['search-input']}
                value={searchText}
                onValueChange={(newValue) => onSearchChange(newValue ?? '')}
                placeholder="Type for search"
                debounceDelay={500}
            />
            {resetCaption && (
                <FlexRow padding="18">
                    <LinkButton
                        size="42"
                        caption={resetCaption}
                        isDisabled={!activeEntity}
                        onClick={onReset}
                    />
                </FlexRow>
            )}
            <VirtualList
                cx={styles['virtual-list']}
                rows={visibleRows}
                value={listState}
                onValueChange={setListState}
                rowsCount={items.length}
                onScroll={(value) =>
                    handleScroll(value.clientHeight, value.scrollHeight, value.scrollTop)
                }
            />
            <div className={styles['sidepanel-footer']}>
                {renderCreateBtn({ onCreated: handleEntityCreated })}
            </div>
        </div>
    );
};
