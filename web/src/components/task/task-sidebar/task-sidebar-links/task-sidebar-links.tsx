import { Accordion, Spinner } from '@epam/loveship';
import { DocumentLink, DocumentLinkWithName } from 'api/hooks/annotations';
import { Category, FileDocument } from 'api/typings';
import React, { useEffect, useMemo } from 'react';

import styles from './task-sidebar-links.module.scss';

interface TaskSidebarLinksProps {
    categories?: Category[];
    searchText: string;
    setSearchText: (text: string) => void;
    documentLinks?: DocumentLinkWithName[];
    onLinkChanged: (documentId: number, categoryId: string) => void;
    onRelatedDocClick: (documentId?: number) => void;
    selectedRelatedDoc?: FileDocument;
    linksFromApi?: DocumentLink[];
}

export const TaskSidebarLinks: React.FC<TaskSidebarLinksProps> = ({
    categories,
    documentLinks,
    onRelatedDocClick
}) => {
    useEffect(() => {
        return function cleanSelectedDoc() {
            onRelatedDocClick(undefined);
        };
    }, []);
    const linksToShow = useMemo(() => {
        return categories ? (
            categories.map((category) => (
                <Accordion key={category.id} title={category.name} mode="inline">
                    <div className={styles.documents}>
                        {documentLinks
                            ?.filter((docLink) => docLink.category === category.id)
                            .map((docLink) => (
                                <div
                                    key={docLink.to}
                                    className={styles.documents}
                                    role="none"
                                    onClick={() => onRelatedDocClick(docLink.to)}
                                >
                                    {docLink.documentName}
                                </div>
                            ))}
                    </div>
                </Accordion>
            ))
        ) : (
            <Spinner color="sky" />
        );
    }, [documentLinks, categories]);

    return (
        <div className={styles.container}>
            <p className={styles.text}> Select links between documents</p>
            {linksToShow}
        </div>
    );
};
