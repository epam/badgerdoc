import React, { FC, useEffect, useMemo, useRef, useState } from 'react';
import { AnnotationRow } from './annotationRow';
import { Annotation } from 'shared';
import {
    ANNOTATION_FLOW_ITEM_ID_PREFIX,
    ANNOTATION_LABEL_ID_PREFIX
} from 'shared/constants/annotations';

import { ReactComponent as goLastIcon } from '@epam/assets/icons/common/navigation-chevron-down_down-18.svg';
import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { ReactComponent as goFirstIcon } from '@epam/assets/icons/common/navigation-chevron-up_up-18.svg';
import { collectIncomingLinks } from './utils';
import { Link } from 'api/typings';

import { Button, FlexRow, Text } from '@epam/loveship';
import styles from './task-sidebar-flow.module.scss';

export const AnnotationList: FC<{
    list: Annotation[];
    isEditable: boolean;
    selectedAnnotationId?: Annotation['id'];
    onLinkDeleted: (pageNum: number, annotationId: Annotation['id'], link: Link) => void;
    onAnnotationDeleted: (pageNum: number, annotationId: Annotation['id']) => void;
    onSelect: (annotation: Annotation) => void;
}> = ({ list, isEditable, selectedAnnotationId, onSelect, onLinkDeleted, onAnnotationDeleted }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isSelectedInCurrentView, setIsSelectedInCurrentView] = useState<boolean>(false);

    useEffect(() => {
        if (!selectedAnnotationId) {
            setIsSelectedInCurrentView(false);
            return;
        }

        const index = list.findIndex(({ id }) => id === selectedAnnotationId);

        setSelectedIndex(index);
        setIsSelectedInCurrentView(index !== -1);

        containerRef.current
            ?.querySelector(`#${ANNOTATION_FLOW_ITEM_ID_PREFIX}${selectedAnnotationId}`)
            ?.scrollIntoView();
    }, [list, selectedAnnotationId]);

    const handleSelect = (index: number) => {
        const selectedAnnotation = list[index];
        setSelectedIndex(index);
        onSelect(selectedAnnotation);

        // TODO: need to extract this logic to the place
        // where this scrolling is really needed.
        // For PDF-related case (when only 1 PDF doc is opened) it's not
        // needed - in this case this scrolling will not do anything
        document
            .querySelector(`#${ANNOTATION_LABEL_ID_PREFIX}${selectedAnnotation.id}`)
            ?.scrollIntoView();
    };

    const handleSelectById = (id: Annotation['id']) => {
        const index = list.findIndex((item) => item.id === id);
        handleSelect(index);
    };

    const handleGoPrev = () => {
        const prevIndex = !selectedIndex ? 0 : selectedIndex - 1;
        handleSelect(prevIndex);
    };

    const handleGoNext = () => {
        const nextIndex = selectedIndex === list.length - 1 ? selectedIndex : selectedIndex + 1;
        handleSelect(nextIndex);
    };

    const isOnFirstElement = !selectedIndex || !isSelectedInCurrentView;
    const isOnLastElement = !isSelectedInCurrentView || selectedIndex === list.length - 1;

    const { incomingLinksByAnnotationId, annotationNameById } = useMemo(
        () => collectIncomingLinks(list),
        [list]
    );

    return (
        <>
            <FlexRow cx={styles.toolbar}>
                <Button
                    size="24"
                    fill="white"
                    icon={goLastIcon}
                    cx={styles.button}
                    isDisabled={!list.length || selectedIndex === list.length - 1}
                    onClick={() => handleSelect(list.length - 1)}
                />
                <Button
                    size="24"
                    fill="white"
                    icon={goNextIcon}
                    cx={styles.button}
                    onClick={handleGoNext}
                    isDisabled={isOnLastElement}
                    rawProps={{ 'data-testid': 'flow-next-button' }}
                />
                <Button
                    size="24"
                    fill="white"
                    icon={goPrevIcon}
                    cx={styles.button}
                    onClick={handleGoPrev}
                    isDisabled={isOnFirstElement}
                />
                <Button
                    size="24"
                    fill="white"
                    icon={goFirstIcon}
                    cx={styles.button}
                    onClick={() => handleSelect(0)}
                    isDisabled={isOnFirstElement}
                    rawProps={{ 'data-testid': 'flow-prev-button' }}
                />
                {!isSelectedInCurrentView ? null : (
                    <Text color="night500" cx={styles.counter}>
                        {selectedIndex + 1} of {list.length}
                    </Text>
                )}
            </FlexRow>
            <div className={styles.listContainer} ref={containerRef}>
                {list.map((annotation, index) => (
                    <AnnotationRow
                        {...annotation}
                        index={index}
                        isEditable={isEditable}
                        key={`${annotation.id}-${index}`}
                        onLinkDeleted={onLinkDeleted}
                        annotationNameById={annotationNameById}
                        incomingLinks={incomingLinksByAnnotationId[annotation.id]}
                        onSelect={handleSelect}
                        onSelectById={handleSelectById}
                        selectedAnnotationId={selectedAnnotationId}
                        onCloseIconClick={onAnnotationDeleted}
                    />
                ))}
            </div>
        </>
    );
};
