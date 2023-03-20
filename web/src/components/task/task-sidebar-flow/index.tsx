import React, { FC, useEffect, useMemo, useState } from 'react';
import { FlexRow, Panel, TabButton } from '@epam/loveship';
import styles from './styles.module.scss';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { AnnotationList } from './annotation-list';
import { Annotation } from 'shared';
import { getSortedAllAnnotationList, getSortedAnnotationsByUserId, getTabs } from './utils';
import { OWNER_TAB } from './constants';

export const FlowSideBar: FC = () => {
    const [currentTab, setCurrentTab] = useState(OWNER_TAB.id);

    const {
        taskUsers,
        annotationsByUserId,
        setSelectedAnnotation,
        setCurrentDocumentUserId,
        currentDocumentUserId = OWNER_TAB.id,
        allAnnotations: allAnnotationsByPageNum = {},
        selectedAnnotation: { id: selectedAnnotationId } = {}
    } = useTaskAnnotatorContext();

    useEffect(() => {
        setCurrentTab(currentDocumentUserId);
    }, [currentDocumentUserId]);

    const handleChangeTab = (tab: string) => {
        setCurrentTab(tab);
        setCurrentDocumentUserId(tab === OWNER_TAB.id ? undefined : tab);
    };

    const tabs = useMemo(
        () => getTabs(taskUsers.current.annotators, Object.keys(annotationsByUserId)),
        [taskUsers.current.annotators, annotationsByUserId]
    );

    const allSortedAnnotations = useMemo(
        () => getSortedAllAnnotationList(allAnnotationsByPageNum),
        [allAnnotationsByPageNum]
    );

    const sortedAnnotationsByUserId = useMemo(
        () => getSortedAnnotationsByUserId(annotationsByUserId),
        [annotationsByUserId]
    );

    const annotationsByTab: Record<string, Annotation[]> = {
        ...sortedAnnotationsByUserId,
        [OWNER_TAB.id]: allSortedAnnotations
    };

    return (
        <Panel background="white">
            {tabs.length > 1 && (
                <FlexRow>
                    {tabs.map(({ id, caption }) => (
                        <TabButton
                            key={id}
                            size="36"
                            cx={styles.tab}
                            caption={caption}
                            isLinkActive={currentTab === id}
                            onClick={() => handleChangeTab(id)}
                        />
                    ))}
                </FlexRow>
            )}
            <AnnotationList
                onSelect={setSelectedAnnotation}
                list={annotationsByTab[currentTab]}
                selectedAnnotationId={selectedAnnotationId}
            />
        </Panel>
    );
};
