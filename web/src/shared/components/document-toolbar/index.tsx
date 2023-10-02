import { FC, useCallback } from 'react';
import { FlexRow } from '@epam/uui-components';
import { Button, FlexCell, PickerInput } from '@epam/loveship';
import styles from './styles.module.scss';
import { useArrayDataSource } from '@epam/uui';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';

export const DocumentToolbar: FC<{ countOfPages: number }> = ({ countOfPages }) => {
    const { currentOrderPageNumber, pageNumbers, onCurrentPageChange } = useTaskAnnotatorContext();
    const isLastPage = currentOrderPageNumber === countOfPages - 1;
    const isFirstPage = currentOrderPageNumber === 0;

    const pagesDataSource = useArrayDataSource(
        {
            items: Array.from({ length: countOfPages }).map((_, index) => index + 1),
            getId: (item) => item
        },
        []
    );

    const onPageChange = (selectedPageNumber: number) => {
        const pageOrderNumber = selectedPageNumber - 1;

        onCurrentPageChange(pageNumbers[pageOrderNumber], pageOrderNumber);
    };

    const handleGoNext = useCallback(() => {
        const nextOrderNumber = isLastPage ? countOfPages - 1 : currentOrderPageNumber + 1;

        onCurrentPageChange(pageNumbers[nextOrderNumber], nextOrderNumber);
    }, [isLastPage, countOfPages, currentOrderPageNumber, onCurrentPageChange, pageNumbers]);

    const handleGoPrev = useCallback(() => {
        const nextOrderNumber = isFirstPage ? 0 : currentOrderPageNumber - 1;

        onCurrentPageChange(pageNumbers[nextOrderNumber], nextOrderNumber);
    }, [isFirstPage, currentOrderPageNumber, onCurrentPageChange, pageNumbers]);

    return (
        <FlexRow cx={styles['goto-page-selector']}>
            <FlexCell minWidth={60}>
                <span>Go to page</span>
            </FlexCell>
            <PickerInput
                minBodyWidth={52}
                size="24"
                dataSource={pagesDataSource}
                value={currentOrderPageNumber + 1}
                onValueChange={onPageChange}
                getName={(item) => String(item)}
                selectionMode="single"
                disableClear={true}
            />
            <FlexRow>
                <span>of {countOfPages}</span>
                <Button
                    size="24"
                    fill="white"
                    icon={goPrevIcon}
                    cx={styles.button}
                    onClick={handleGoPrev}
                    isDisabled={isFirstPage}
                />
                <Button
                    size="24"
                    fill="white"
                    icon={goNextIcon}
                    cx={styles.button}
                    onClick={handleGoNext}
                    isDisabled={isLastPage}
                />
            </FlexRow>
        </FlexRow>
    );
};
