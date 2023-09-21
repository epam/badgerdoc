import React, { FC, useEffect, useMemo, useState } from 'react';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { AnnotationList } from './annotation-list';
import { getTabs, getSortedAllAnnotationList } from './utils';
import { OWNER_TAB, VISIBILITY_SETTING_ID } from './constants';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-chevron-left_left-18.svg';
import { ReactComponent as openIcon } from '@epam/assets/icons/common/navigation-chevron-right_right-18.svg';
import { Button, FlexRow, Panel, TabButton, Tooltip } from '@epam/loveship';
import styles from './task-sidebar-flow.module.scss';
import { useLabels } from 'shared/hooks/use-labels';

export const FlowSideBar: FC = () => {
    const [isHidden, setIsHidden] = useState<boolean>(() => {
        const savedValue = localStorage.getItem(VISIBILITY_SETTING_ID);
        return savedValue ? JSON.parse(savedValue) : false;
    });

    const {
        isSplitValidation,
        setSelectedAnnotation,
        job: { annotators } = {},
        setCurrentDocumentUserId,
        latestRevisionByAnnotatorsWithBounds,
        currentDocumentUserId = OWNER_TAB.id,
        allAnnotations: allAnnotationsByPageNum = {},
        selectedAnnotation
    } = useTaskAnnotatorContext();

    const { currentTab, setCurrentTab } = useLabels();

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

    const tabs = useMemo(() => {
        if (!annotators) return [];

        return getTabs({
            users: annotators,
            userIds: Object.keys(latestRevisionByAnnotatorsWithBounds)
        });
    }, [annotators, latestRevisionByAnnotatorsWithBounds]);

    const allSortedAnnotations = useMemo(
        () => getSortedAllAnnotationList(allAnnotationsByPageNum),
        [allAnnotationsByPageNum]
    );

    const annotationsByTab = {
        ...latestRevisionByAnnotatorsWithBounds,
        [OWNER_TAB.id]: allSortedAnnotations
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
                        <FlexRow borderBottom="night400" cx={`${styles['tabs-title-group']}`}>
                            {tabs.map(({ id, caption }) => (
                                <Tooltip
                                    content={id === OWNER_TAB.id ? null : caption}
                                    placement="top"
                                    key={id}
                                >
                                    <TabButton
                                        size="36"
                                        cx={`${styles.tab} ${
                                            currentTab === id ? styles.active : null
                                        }`}
                                        caption={caption}
                                        isLinkActive={currentTab === id}
                                        onClick={() => handleChangeTab(id)}
                                    />
                                </Tooltip>
                            ))}
                        </FlexRow>
                    )}
                    {annotationsByTab[currentTab] && (
                        <AnnotationList
                            onSelect={setSelectedAnnotation}
                            list={annotationsByTab[currentTab]}
                            isEditable={currentTab === OWNER_TAB.id}
                            selectedAnnotation={selectedAnnotation}
                        />
                    )}
                </Panel>
            )}
        </Panel>
    );
};
