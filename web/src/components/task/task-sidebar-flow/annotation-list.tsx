// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { FC, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnnotationRow } from './annotationRow';
import { Annotation, Maybe } from 'shared';
import {
    ANNOTATION_FLOW_ITEM_ID_PREFIX,
    ANNOTATION_LABEL_ID_PREFIX
} from 'shared/constants/annotations';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

import { ReactComponent as goLastIcon } from '@epam/assets/icons/common/navigation-chevron-down_down-18.svg';
import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { ReactComponent as goFirstIcon } from '@epam/assets/icons/common/navigation-chevron-up_up-18.svg';
import { collectIncomingLinks } from './utils';

import { Button, FlexRow, Text, TextPlaceholder } from '@epam/loveship';
import styles from './task-sidebar-flow.module.scss';
import { NoData } from 'shared/no-data';
import { scrollIntoViewIfNeeded } from 'shared/helpers/scroll-into-view-if-needed';

export type AnnotationListProps = {
    list: Annotation[];
    isEditable: boolean;
    selectedAnnotation: Maybe<Annotation>;
    onSelect: (annotation: Annotation) => void;
};

const AnnotationCounter: FC<{ selectedAnnotation: Annotation }> = ({ selectedAnnotation }) => {
    const { allAnnotations, pageNumbers } = useTaskAnnotatorContext();
    const annotationsForPage = allAnnotations![selectedAnnotation.pageNum!];
    const selectedAnnotationIndexPerPage = annotationsForPage.findIndex(
        ({ id }) => selectedAnnotation.id === id
    );
    const uiPageNumber = pageNumbers.findIndex(
        (pageNumber) => pageNumber === selectedAnnotation.pageNum
    );

    return (
        <Text color="night500" cx={styles.counter}>
            Page {uiPageNumber + 1} : {selectedAnnotationIndexPerPage + 1} of{' '}
            {annotationsForPage.length}
        </Text>
    );
};

const AnnotationListPlaceholder: FC<{ countOfItems: number }> = ({ countOfItems }) => {
    const items = useMemo(() => Array.from({ length: countOfItems }), [countOfItems]);

    return (
        <div className={styles['annotation-list-container']}>
            {items.map((_, index) => (
                <div key={index} className={styles.item}>
                    <div className={styles['placeholder-header']}>
                        <TextPlaceholder cx={styles['placeholder-header__item']}></TextPlaceholder>
                    </div>
                    <div className={styles['placeholder-content']}>
                        <TextPlaceholder
                            cx={styles['placeholder-content__item']}
                            wordsCount={9}
                        ></TextPlaceholder>
                    </div>
                </div>
            ))}
        </div>
    );
};

export const AnnotationList: FC<AnnotationListProps> = ({
    list,
    isEditable,
    selectedAnnotation,
    onSelect
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isSelectedInCurrentView, setIsSelectedInCurrentView] = useState<boolean>(false);
    const { areLatestAnnotationsFetching, onLinkDeleted, onAnnotationDeleted, allAnnotations } =
        useTaskAnnotatorContext();
    const { incomingLinksByAnnotationId, annotationNameById } = useMemo(
        () => collectIncomingLinks(list),
        [list]
    );

    useEffect(() => {
        if (!selectedAnnotation) {
            setIsSelectedInCurrentView(false);
            return;
        }

        const index = list.findIndex(({ id }) => id === selectedAnnotation.id);

        setSelectedIndex(index);
        setIsSelectedInCurrentView(index !== -1);

        const annotationItemElement = containerRef.current?.querySelector(
            `#${ANNOTATION_FLOW_ITEM_ID_PREFIX}${selectedAnnotation.id}`
        );

        if (containerRef.current && annotationItemElement) {
            scrollIntoViewIfNeeded(containerRef.current, annotationItemElement);
        }
    }, [list, selectedAnnotation]);

    const handleSelect = useCallback(
        (index: number) => {
            const newSelectedAnnotation = list[index];
            setSelectedIndex(index);
            onSelect(newSelectedAnnotation);

            // TODO: need to extract this logic to the place
            // where this scrolling is really needed.
            // For PDF-related case (when only 1 PDF doc is opened) it's not
            // needed - in this case this scrolling will not do anything
            document
                .querySelector(`#${ANNOTATION_LABEL_ID_PREFIX}${newSelectedAnnotation.id}`)
                ?.scrollIntoView();
        },
        [list, onSelect]
    );

    const handleSelectById = useCallback(
        (id: Annotation['id']) => {
            const index = list.findIndex((item) => item.id === id);
            handleSelect(index);
        },
        [handleSelect, list]
    );

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
                {!!selectedAnnotation && allAnnotations![selectedAnnotation.pageNum!] && (
                    <AnnotationCounter selectedAnnotation={selectedAnnotation}></AnnotationCounter>
                )}
            </FlexRow>
            <div className={styles['annotation-container']} ref={containerRef}>
                {areLatestAnnotationsFetching ? (
                    <AnnotationListPlaceholder countOfItems={5}></AnnotationListPlaceholder>
                ) : list.length === 0 ? (
                    <NoData title="No annotations for the viewed pages" />
                ) : (
                    list.map((annotation, index) => (
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
                            selectedAnnotationId={selectedAnnotation?.id}
                            onCloseIconClick={onAnnotationDeleted}
                        />
                    ))
                )}
            </div>
        </>
    );
};
