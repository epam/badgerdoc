import React, { FC, useEffect, useState } from 'react';
import { DocumentLinkWithName } from 'api/hooks/annotations';
import { useCategoriesByJob } from 'api/hooks/categories';
import { TaskSidebarLabels } from 'components/task/task-sidebar-labels/task-sidebar-labels';
import { TaskSidebarLinks } from '../task-sidebar-links/task-sidebar-links';
import { useNotifications } from 'shared/components/notifications';
import { Category, FileDocument, Filter, Label, Operators, SortingDirection } from 'api/typings';
import { getError } from 'shared/helpers/get-error';
import { FlexCell } from '@epam/uui-components';
import { MultiSwitch, Text } from '@epam/loveship';

import styles from './task-sidebar-labels-links.module.scss';

type TaskSidebarLabelsLinksProps = {
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

    const categoryTypeFilter: Filter<keyof Category> = {
        field: 'type',
        operator: Operators.EQ,
        value: documentCategoryType
    };

    const {
        data: categories,
        isError,
        refetch: refetchCategories
    } = useCategoriesByJob(
        {
            page: 1,
            size: 100,
            sortConfig: { field: 'name', direction: SortingDirection.ASC },
            searchText,
            filters: [categoryTypeFilter],
            jobId
        },
        { enabled: !!jobId }
    );
    const { notifyError } = useNotifications();
    if (isError) {
        notifyError(<Text>{getError(isError)}</Text>);
    }

    const handleCategoryTypeChange = (type: DocumentCategoryType) => {
        setDocumentCategoryType(type);
        setSearchText('');
    };

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
                    labels={categories?.data}
                    onLabelsSelected={onLabelsSelected}
                    selectedLabels={selectedLabels ?? []}
                    searchText={searchText}
                    setSearchText={setSearchText}
                />
            ) : (
                <TaskSidebarLinks
                    categories={categories?.data}
                    documentLinks={documentLinks}
                    onRelatedDocClick={onRelatedDocClick}
                    selectedRelatedDoc={selectedRelatedDoc}
                />
            )}
        </FlexCell>
    );
};
