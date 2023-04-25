import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';
import { Button, FlexRow, Panel, TabButton } from '@epam/loveship';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { AnnotationList } from './annotation-list';
import {
    getTabs,
    getCategoriesByUserId,
    getSortedAllAnnotationList,
    getSortedAnnotationsByUserId
} from './utils';
import { OWNER_TAB, VISIBILITY_SETTING_ID } from './constants';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-chevron-left_left-18.svg';
import { ReactComponent as openIcon } from '@epam/assets/icons/common/navigation-chevron-right_right-18.svg';

import styles from './styles.module.scss';
import { Label } from 'api/typings';

export const FlowSideBar: FC = () => {
    const [currentTab, setCurrentTab] = useState(OWNER_TAB.id);
    const [isHidden, setIsHidden] = useState<boolean>(() => {
        const savedValue = localStorage.getItem(VISIBILITY_SETTING_ID);
        return savedValue ? JSON.parse(savedValue) : false;
    });

    const {
        userPages,
        categories,
        setTabValue,
        onLinkDeleted,
        selectedLabels,
        onLabelsSelected,
        isSplitValidation,
        annotationsByUserId,
        setSelectedAnnotation,
        job: { annotators } = {},
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

    const handleToggleVisibility = () => {
        localStorage.setItem(VISIBILITY_SETTING_ID, String(!isHidden));
        setIsHidden(!isHidden);
    };

    const handleLabelSelect = useCallback(
        (label: Label) => {
            const isExisted = selectedLabels.some(({ id }) => id === label.id);

            if (!isExisted) {
                setTabValue('Document');
                onLabelsSelected([...selectedLabels, label]);
            }
        },
        [onLabelsSelected, selectedLabels]
    );

    const handleLabelDelete = useCallback(
        (label: Label) => {
            const withoutCurrentLabel = selectedLabels.filter(({ id }) => id !== label.id);
            onLabelsSelected(withoutCurrentLabel);
        },
        [onLabelsSelected, selectedLabels]
    );

    const tabs = useMemo(() => {
        if (!annotators) return [];

        return getTabs({
            users: annotators,
            userIds: Object.keys(annotationsByUserId)
        });
    }, [annotators, annotationsByUserId]);

    const allSortedAnnotations = useMemo(
        () => getSortedAllAnnotationList(allAnnotationsByPageNum),
        [allAnnotationsByPageNum]
    );

    const sortedAnnotationsByUserId = useMemo(
        () => getSortedAnnotationsByUserId(annotationsByUserId),
        [annotationsByUserId]
    );

    const categoriesByUserId = useMemo(
        () => getCategoriesByUserId(userPages, categories),
        [userPages, categories]
    );

    const annotationsByTab = {
        ...sortedAnnotationsByUserId,
        [OWNER_TAB.id]: allSortedAnnotations
    };

    const labelsByTab = {
        ...categoriesByUserId,
        [OWNER_TAB.id]: selectedLabels
    };

    const isTabsShown = isSplitValidation && tabs.length > 1;

    return (
        <Panel cx={styles.wrapper}>
            <Button
                fill="none"
                cx={styles.hideIcon}
                onClick={handleToggleVisibility}
                icon={isHidden ? openIcon : closeIcon}
            />
            {!isHidden && (
                <Panel background="white" cx={styles.container}>
                    {isTabsShown && (
                        <FlexRow borderBottom="night400">
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
                    {annotationsByTab[currentTab] && (
                        <AnnotationList
                            onLabelDelete={handleLabelDelete}
                            onLabelSelect={handleLabelSelect}
                            isOwner={currentTab === OWNER_TAB.id}
                            onLinkDeleted={onLinkDeleted}
                            onSelect={setSelectedAnnotation}
                            labels={labelsByTab[currentTab]}
                            list={annotationsByTab[currentTab]}
                            isEditable={currentTab === OWNER_TAB.id}
                            selectedAnnotationId={selectedAnnotationId}
                        />
                    )}
                </Panel>
            )}
        </Panel>
    );
};
