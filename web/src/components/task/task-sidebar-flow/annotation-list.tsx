import React, { FC, useEffect, useRef, useState } from 'react';
import { Button, ControlGroup, FlexRow, Text } from '@epam/loveship';
import styles from './styles.module.scss';
import { ScrollBars } from '@epam/uui-components';
import { ReactComponent as leftIcon } from '@epam/assets/icons/common/navigation-chevron-left-18.svg';
import { ReactComponent as rightIcon } from '@epam/assets/icons/common/navigation-chevron-right-18.svg';
import { AnnotationRow } from './annotation';
import { Annotation } from 'shared';
import {
    ANNOTATION_FLOW_ITEM_ID_PREFIX,
    ANNOTATION_LABEL_ID_PREFIX
} from 'shared/constants/annotations';

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

    return (
        <>
            <FlexRow cx={styles.toolbar}>
                <ControlGroup>
                    <Button
                        fill="white"
                        icon={leftIcon}
                        onClick={handleGoPrev}
                        rawProps={{ 'data-testid': 'flow-prev-button' }}
                        isDisabled={!selectedIndex || !isSelectedInCurrentView}
                    />
                    <Button
                        fill="white"
                        icon={rightIcon}
                        onClick={handleGoNext}
                        rawProps={{ 'data-testid': 'flow-next-button' }}
                        isDisabled={!isSelectedInCurrentView || selectedIndex === list.length - 1}
                    />
                </ControlGroup>
                {!isSelectedInCurrentView ? null : (
                    <Text color="night500">
                        {selectedIndex + 1} of {list.length}
                    </Text>
                )}
            </FlexRow>
            <ScrollBars>
                <div className={styles.container} ref={containerRef}>
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
            </ScrollBars>
        </>
    );
};
