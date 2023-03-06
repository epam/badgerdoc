import React, { FC, useCallback, useEffect, useState } from 'react';
import { DocumentLinkWithName } from 'api/hooks/annotations';
import { useCategoriesByJob } from 'api/hooks/categories';
import { TaskSidebarLabels } from 'components/task/task-sidebar-labels/task-sidebar-labels';
import { TaskSidebarLinks } from '../task-sidebar-links/task-sidebar-links';
import { useNotifications } from 'shared/components/notifications';
import {
    Category,
    FileDocument,
    FilterWithDocumentExtraOption,
    Label,
    Operators,
    SortingDirection
} from 'api/typings';
import { getError } from 'shared/helpers/get-error';
import { FlexCell } from '@epam/uui-components';
import { MultiSwitch, Text } from '@epam/loveship';

import styles from './task-sidebar-labels-links.module.scss';

type TaskSidebarLabelsLinksProps = {
    viewMode: boolean;
    jobId?: number;
    onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
    selectedLabels: Label[];
    documentLinks?: DocumentLinkWithName[];
    onRelatedDocClick: (documentId?: number) => void;
    selectedRelatedDoc?: FileDocument;
};
export enum DocumentCategoryType {
    Document = 'document',
    DocumentLabel = 'document_link'
}
const documentCategories = [
    { id: DocumentCategoryType.Document, caption: 'Labels', cx: `${styles.categoriesAndLinks}` },
    { id: DocumentCategoryType.DocumentLabel, caption: 'Links', cx: `${styles.categoriesAndLinks}` }
];
export const TaskSidebarLabelsLinks: FC<TaskSidebarLabelsLinksProps> = ({
    viewMode = false,
    jobId,
    onLabelsSelected,
    selectedLabels,
    documentLinks,
    onRelatedDocClick,
    selectedRelatedDoc
}) => {
    const [documentCategoryType, setDocumentCategoryType] = useState<DocumentCategoryType>(
        DocumentCategoryType.Document
    );

    const [searchText, setSearchText] = useState('');

    const categoryTypeFilter: FilterWithDocumentExtraOption<keyof Category> = {
        field: 'type',
        operator: Operators.EQ,
        value: documentCategoryType
    };

    const {
        data: { pages: categories } = {},
        isError,
        isFetching,
        hasNextPage,
        fetchNextPage,
        refetch: refetchCategories
    } = useCategoriesByJob(
        {
            size: 100,
            sortConfig: { field: 'name', direction: SortingDirection.ASC },
            searchText,
            filters: [categoryTypeFilter],
            jobId
        },
        { enabled: Boolean(jobId) }
    );
    const { notifyError } = useNotifications();
    if (isError) {
        notifyError(<Text>{getError(isError)}</Text>);
    }

    const handleCategoryTypeChange = (type: DocumentCategoryType) => {
        setDocumentCategoryType(type);
        setSearchText('');
    };

    const handleLoadNextPage = useCallback(() => {
        if (!isFetching) {
            fetchNextPage();
        }
    }, [isFetching, fetchNextPage]);

    useEffect(() => {
        if (searchText || documentCategoryType) {
            refetchCategories();
        }
    }, [searchText, documentCategoryType]);

    return (
        <FlexCell cx={styles.linksAndLabels}>
            <MultiSwitch
                items={documentCategories}
                value={documentCategoryType}
                onValueChange={handleCategoryTypeChange}
            />

            {documentCategoryType === DocumentCategoryType.Document ? (
                <TaskSidebarLabels
                    isLoading={isFetching}
                    hasNextPage={Boolean(hasNextPage)}
                    onFetchNext={handleLoadNextPage}
                    viewMode={viewMode}
                    labels={categories}
                    onLabelsSelected={onLabelsSelected}
                    selectedLabels={selectedLabels ?? []}
                    searchText={searchText}
                    setSearchText={setSearchText}
                />
            ) : (
                <TaskSidebarLinks
                    categories={categories}
                    documentLinks={documentLinks}
                    onRelatedDocClick={onRelatedDocClick}
                    selectedRelatedDoc={selectedRelatedDoc}
                />
            )}
        </FlexCell>
    );
};
