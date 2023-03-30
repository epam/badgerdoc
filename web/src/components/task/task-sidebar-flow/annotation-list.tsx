import React, { FC, useEffect, useRef, useState } from 'react';
import { Button, FlexRow, Text } from '@epam/loveship';
import { AnnotationRow } from './annotation';
import { Annotation } from 'shared';
import {
    ANNOTATION_FLOW_ITEM_ID_PREFIX,
    ANNOTATION_LABEL_ID_PREFIX
} from 'shared/constants/annotations';

import styles from './styles.module.scss';
import { ReactComponent as goLastIcon } from '@epam/assets/icons/common/navigation-chevron-down_down-18.svg';
import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { ReactComponent as goFirstIcon } from '@epam/assets/icons/common/navigation-chevron-up_up-18.svg';

export const AnnotationList: FC<{
    list: Annotation[];
    selectedAnnotationId?: Annotation['id'];
    onSelect: (annotation: Annotation) => void;
}> = ({ list, selectedAnnotationId, onSelect }) => {
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

        document
            .querySelector(`#${ANNOTATION_LABEL_ID_PREFIX}${selectedAnnotation.id}`)
            ?.scrollIntoView();
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
                        key={annotation.id}
                        onSelect={handleSelect}
                        selectedAnnotationId={selectedAnnotationId}
                    />
                ))}
            </div>
        </>
    );
};
