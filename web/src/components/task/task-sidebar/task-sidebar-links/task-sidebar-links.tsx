import { Accordion, Spinner } from '@epam/loveship';
import { DocumentLinkWithName } from 'api/hooks/annotations';
import { Category, FileDocument } from 'api/typings';
import React, { useEffect, useMemo } from 'react';

import styles from './task-sidebar-links.module.scss';

interface TaskSidebarLinksProps {
    categories?: Category[];
    documentLinks?: DocumentLinkWithName[];
    onRelatedDocClick: (documentId?: number) => void;
    selectedRelatedDoc?: FileDocument;
}

export const TaskSidebarLinks: React.FC<TaskSidebarLinksProps> = ({
    categories,
    documentLinks,
    onRelatedDocClick,
    selectedRelatedDoc
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
                                    className={`${styles.document} ${
                                        docLink.to === selectedRelatedDoc?.id ? styles.selected : ''
                                    }`}
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
    }, [documentLinks, categories, selectedRelatedDoc]);

    return (
        <div className={styles.container}>
            <p className={styles.text}> Select links between documents</p>
            {linksToShow}
        </div>
    );
};
