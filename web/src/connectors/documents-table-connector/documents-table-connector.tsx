// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { useEffect, useMemo, useRef, useState, useContext } from 'react';
import styles from './documents-table-connector.module.scss';
import {
    Button,
    Checkbox,
    DataTable,
    ErrorNotification,
    FlexRow,
    SuccessNotification,
    Text
} from '@epam/loveship';
import {
    Dataset,
    FileDocument,
    FilterWithDocumentExtraOption,
    Operators,
    SortingDirection
} from '../../api/typings';
import { useDeleteFilesMutation, useDocuments } from '../../api/hooks/documents';
import { TableWrapper, usePageTable } from 'shared';
import { pageSizes } from 'shared/primitives';
import { documentColumns } from './documents-columns';
import { useAsyncSourceTable } from '../../shared/hooks/async-source-table';
import {
    useColumnPickerFilter,
    useDateRangeFilter
} from '../../shared/components/filters/column-picker';
import { INotification, useLazyDataSource, useUuiContext } from '@epam/uui';
import { documentNamesFetcher } from '../../api/hooks/document';
import { createPagingCachedLoader } from '../../shared/helpers/create-paging-cached-loader';
import { DocumentCardViewItem } from 'components/documents/document-card-view-item/document-card-view-item';
import { FileJobs, fileJobsFetcher } from '../../api/hooks/annotations';
import { DocumentsSearch } from 'shared/contexts/documents-search';
import { useThumbnail } from 'api/hooks/assets';
import { ReactComponent as PlusIcon } from '@epam/assets/icons/common/action-add-18.svg';
import { ReactComponent as ListPlusIcon } from '@epam/assets/icons/common/media-playlist-add-18.svg';
import { ReactComponent as PreprocessorIcon } from '@epam/assets/icons/common/navigation-refresh-18.svg';
import { ReactComponent as DeleteIcon } from '@epam/assets/icons/common/action-delete-18.svg';
import { DatasetChooseForm, DatasetWithFiles } from '../../components';
import { getError } from '../../shared/helpers/get-error';
import { useAddFilesToDatasetMutation } from '../../api/hooks/datasets';
import { saveFiltersToStorage } from '../../shared/helpers/set-filters';

type DocumentsTableConnectorProps = {
    dataset?: Dataset | null | undefined;
    onRowClick: (id: number) => void;
    fileIds?: number[];
    isJobPage?: boolean;
    handleJobAddClick: (selectedFiles: number[]) => void;
    withHeader?: boolean;
};

export const DocumentsTableConnector: React.FC<DocumentsTableConnectorProps> = ({
    dataset,
    onRowClick,
    fileIds,
    isJobPage,
    handleJobAddClick,
    withHeader
}) => {
    const {
        pageConfig,
        setPageConfig,
        onPageChange,
        totalCount,
        onTotalCountChange,
        tableValue,
        onTableValueChange,
        setSortConfig,
        sortConfig,
        setFilters,
        filters
    } = usePageTable<FileDocument>('last_modified');
    const { checked } = tableValue;

    const { documentView, documentsSort, query, documentsSortOrder } = useContext(DocumentsSearch);
    const svc = useUuiContext();
    const mutation = useAddFilesToDatasetMutation();
    const deleteFilesMutation = useDeleteFilesMutation();

    const [selectedFiles, setSelectedFiles] = useState<number[]>(fileIds || []);
    const [jobs, setJobs] = useState<FileJobs>();

    console.log('DocumentsTableConnector: selectedFiles:', selectedFiles);
    console.log('DocumentsTableConnector: tableValue.checked:', tableValue.checked);

    const isTableView = isJobPage || documentView === 'table';
    const filtersRef = useRef(filters);
    filtersRef.current = filters;

    const arraysEqual = (a: number[] = [], b: number[] = []) => {
        const setA = new Set(a);
        const setB = new Set(b);
        return a.length === b.length && [...setA].every((id) => setB.has(id));
    };

    useEffect(() => {
        if (fileIds && !arraysEqual(fileIds, selectedFiles)) {
            console.log(
                'DocumentsTableConnector: Initializing selectedFiles with fileIds:',
                fileIds
            );
            setSelectedFiles(fileIds);
        }
    }, [fileIds]);

    useEffect(() => {
        if (!arraysEqual(selectedFiles, tableValue.checked)) {
            console.log('DocumentsTableConnector: Syncing tableValue.checked to:', selectedFiles);
            onTableValueChange({
                ...tableValue,
                checked: [...selectedFiles]
            });
        }
    }, [selectedFiles]);

    useEffect(() => {
        if (checked && !arraysEqual(checked, selectedFiles)) {
            console.log('DocumentsTableConnector: Updating selectedFiles with checked:', checked);
            setSelectedFiles([...checked]);
        }
    }, [checked]);

    useEffect(() => {
        if (!isJobPage) {
            onTableValueChange({ ...tableValue, filter: dataset ? {} : undefined });
        }
    }, [dataset]);

    useEffect(() => {
        let filtersToSet: FilterWithDocumentExtraOption<keyof FileDocument>[] = [];
        if (tableValue.filter) {
            const filters = Object.keys(tableValue.filter);
            filtersToSet = filters.flatMap((item) => {
                const field = item as keyof FileDocument;
                const filter = tableValue.filter![field as keyof FileDocument];
                const operatorsArray = Object.keys(filter!);
                if (operatorsArray.length === 1) {
                    const operator = operatorsArray[0] as Operators;
                    return [
                        {
                            field,
                            operator,
                            value: filter![operator]! as string[]
                        }
                    ];
                } else if ('from' in filter! && 'to' in filter) {
                    return [
                        { field, operator: Operators.GE, value: filter['from'] as string[] },
                        { field, operator: Operators.LE, value: filter['to'] as string[] }
                    ];
                } else {
                    return [];
                }
            });
        }

        if (dataset) {
            filtersToSet.push({
                field: 'datasets.id',
                operator: Operators.EQ,
                value: dataset.id
            });
            saveFiltersToStorage(filtersToSet, 'documents');
            setFilters(filtersToSet);
        }
        if (tableValue.filter) {
            saveFiltersToStorage(filtersToSet, 'documents');
            setFilters(filtersToSet);
        }
    }, [tableValue.filter, dataset]);

    const { data: files, isFetching } = useDocuments(
        {
            page: pageConfig.page,
            size: pageConfig.pageSize,
            filters,
            searchText: query,
            sortConfig: isTableView
                ? sortConfig
                : {
                      direction: documentsSortOrder,
                      field: documentsSort as keyof FileDocument
                  }
        },
        { refetchOnReconnect: false }
    );

    const thumbnails = useThumbnail([...new Set(files?.data.map((file) => file.id))]);

    useEffect(() => {
        if (files?.data) {
            onTotalCountChange(files.pagination.total);
        }
    }, [files?.data]);

    const { dataSource } = useAsyncSourceTable<FileDocument, number>(
        isFetching,
        files?.data ?? [],
        pageConfig.page,
        pageConfig.pageSize,
        query,
        sortConfig,
        filters
    );

    const view = dataSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            checkbox: { isVisible: true },
            isSelectable: true,
            onClick: ({ id }) => onRowClick(id)
        }),
        sortBy: (item, sorting) => {
            const { field, direction } = sorting;
            if (field !== sortConfig?.field || direction !== sortConfig?.direction) {
                setSortConfig({
                    field: field as keyof FileDocument,
                    direction: direction as SortingDirection
                });
            }
        }
    });

    useEffect(() => {
        setPageConfig({ page: 1, pageSize: pageSizes._15 });
    }, [dataset]);

    useEffect(() => () => dataSource.unsubscribeView(onTableValueChange), []);

    useEffect(() => {
        if (files?.data?.length) {
            fileJobsFetcher(files.data.map((e) => e.id)).then((e) => setJobs(e as any));
        }
    }, [files]);

    const namesCache = useRef<PagingCache>({
        page: -1,
        cache: [],
        search: ''
    });

    type PagingCache = {
        page: number;
        cache: Array<string>;
        search: string;
    };

    const loadDocumentNames = createPagingCachedLoader(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await documentNamesFetcher(pageNumber, pageSize, filtersRef.current, keyword)
    );

    const documentNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadDocumentNames,
            getId: (type) => type
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, 'original_name'>(
        documentNames,
        'original_name',
        { showSearch: true }
    );

    const renderLastModifiedFilter = useDateRangeFilter('last_modified');

    const handleSelectAllClick = () => {
        const allFiles = files?.data.map((file) => file.id) || [];
        const isAllSelected = allFiles.every((id) => selectedFiles.includes(id));
        const newSelected = isAllSelected ? [] : allFiles;
        console.log('DocumentsTableConnector: Select all, new selectedFiles:', newSelected);
        setSelectedFiles(newSelected);
    };

    const columns = useMemo(() => {
        const typeColumn = documentColumns.find(({ key }) => key === 'original_name');
        typeColumn!.renderFilter = renderNameFilter;

        const lastModifiedColumn = documentColumns.find(({ key }) => key === 'original_name');
        lastModifiedColumn!.renderFilter = renderLastModifiedFilter;

        return documentColumns;
    }, [renderNameFilter, renderLastModifiedFilter]);

    const onChooseDataset = async (dataset: DatasetWithFiles) => {
        dataset.objects = fileIds || selectedFiles || tableValue.checked || [];
        try {
            await mutation.mutateAsync(dataset);
        } catch (err) {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(err)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
        }
    };

    const showModal = () => {
        return svc.uuiModals
            .show<DatasetWithFiles>((props) => (
                <DatasetChooseForm onChooseDataset={onChooseDataset} {...props} />
            ))
            .then(() => {
                svc.uuiNotifications.show(
                    (props: INotification) => (
                        <SuccessNotification {...props}>
                            <Text>Data has been saved!</Text>
                        </SuccessNotification>
                    ),
                    { duration: 2 }
                );
            });
    };

    const isCardView = documentView === 'card' && files?.data && thumbnails && jobs;

    const handleFileDeleteClick = async () => {
        try {
            await deleteFilesMutation.mutateAsync(selectedFiles);
            onTableValueChange({ ...tableValue, checked: [] });
            setSelectedFiles([]);
        } catch (err) {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(err)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
        }
    };

    const selectionCount = selectedFiles.length;
    const allFilesCount = files?.data?.length || 0;
    const isAllSelected = allFilesCount > 0 && selectionCount === allFilesCount;

    const handleAddToExtraction = () => {
        console.log('DocumentsTableConnector: Submitting selection:', selectedFiles);
        handleJobAddClick(selectedFiles);
    };

    if (isTableView) {
        return (
            <>
                {withHeader && (
                    <FlexRow cx={styles.container}>
                        <FlexRow padding="6">
                            <Checkbox
                                label={
                                    (selectionCount > 0 && `${selectionCount} selected`) ||
                                    'Select All'
                                }
                                value={isAllSelected}
                                onValueChange={handleSelectAllClick}
                                indeterminate={selectionCount > 0 && !isAllSelected}
                            />
                        </FlexRow>
                        <FlexRow padding="6">
                            <Button
                                icon={PlusIcon}
                                caption="Add to dataset"
                                onClick={showModal}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                        <FlexRow padding="6">
                            <Button
                                icon={PreprocessorIcon}
                                caption="Preprocess"
                                onClick={() => {}}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                        <FlexRow padding="6">
                            <Button
                                icon={ListPlusIcon}
                                caption="Add to extraction"
                                onClick={handleAddToExtraction}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                        <div className={styles.divider} />
                        <FlexRow padding="6">
                            <Button
                                icon={DeleteIcon}
                                caption="Delete"
                                onClick={handleFileDeleteClick}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                    </FlexRow>
                )}
                <div className={styles.wrapper}>
                    <TableWrapper
                        page={pageConfig.page || 1}
                        pageSize={pageConfig.pageSize || pageSizes._15}
                        totalCount={totalCount || 0}
                        hasMore={files?.pagination?.has_more ?? false}
                        onPageChange={onPageChange}
                    >
                        <DataTable
                            key={selectedFiles.join(',')}
                            {...view.getListProps()}
                            getRows={view.getVisibleRows}
                            value={tableValue}
                            onValueChange={onTableValueChange}
                            columns={columns}
                            headerTextCase="upper"
                        />
                    </TableWrapper>
                </div>
            </>
        );
    }

    if (isCardView) {
        return (
            <>
                <FlexRow cx={styles.container}>
                    <FlexRow padding="6">
                        <Checkbox
                            label={
                                (selectionCount > 0 && `${selectionCount} selected`) || 'Select All'
                            }
                            value={isAllSelected}
                            onValueChange={handleSelectAllClick}
                            indeterminate={selectionCount > 0 && !isAllSelected}
                        />
                    </FlexRow>
                    <FlexRow padding="6">
                        <Button
                            icon={PlusIcon}
                            caption="Add to dataset"
                            onClick={showModal}
                            fill="light"
                            isDisabled={selectionCount === 0}
                        />
                        <FlexRow padding="6">
                            <Button
                                icon={PreprocessorIcon}
                                caption="Preprocess"
                                onClick={() => {}}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                        <FlexRow padding="6">
                            <Button
                                icon={ListPlusIcon}
                                caption="Add to extraction"
                                onClick={handleAddToExtraction}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                        <div className={styles.divider} />
                        <FlexRow padding="6">
                            <Button
                                icon={DeleteIcon}
                                caption="Delete"
                                onClick={handleFileDeleteClick}
                                fill="light"
                                isDisabled={selectionCount === 0}
                            />
                        </FlexRow>
                    </FlexRow>
                </FlexRow>
                <TableWrapper
                    page={pageConfig.page || 1}
                    pageSize={pageConfig.pageSize || pageSizes._15}
                    totalCount={totalCount || 0}
                    hasMore={files?.pagination?.has_more ?? false}
                    onPageChange={onPageChange}
                >
                    <div className={styles['card-container']}>
                        {files?.data.map(({ id, original_name, last_modified }) => (
                            <DocumentCardViewItem
                                key={id}
                                documentId={+id}
                                documentName={original_name}
                                lastModified={last_modified}
                                jobs={(jobs as any)[id] as any}
                                thumbnails={thumbnails}
                                selectedFiles={selectedFiles}
                                setSelectedFiles={setSelectedFiles}
                            />
                        ))}
                    </div>
                </TableWrapper>
            </>
        );
    }

    return <div />;
};
