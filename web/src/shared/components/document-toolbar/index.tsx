import { FC, SetStateAction, useCallback, useEffect, useState } from 'react';
import { FlexRow } from '@epam/uui-components';
import { Button, PickerInput } from '@epam/loveship';
import styles from './styles.module.scss';
import { useArrayDataSource } from '@epam/uui';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

import { ReactComponent as goNextIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as goPrevIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { DocumentScale } from 'components/documents/document-scale/document-scale';

type TDocumentToolbar = {
    countOfPages: number;
    scale: number;
    onPageChange: (pageOrderNumber: number) => void;
    onScaleChange: (value: SetStateAction<number>) => void;
};

export const DocumentToolbar: FC<TDocumentToolbar> = ({
    countOfPages,
    scale,
    onPageChange,
    onScaleChange
}) => {
    const { currentOrderPageNumber, pageNumbers, onCurrentPageChange } = useTaskAnnotatorContext();
    const isLastPage = currentOrderPageNumber === countOfPages - 1;
    const isFirstPage = currentOrderPageNumber === 0;
    const [pageInputValue, setPageInputValue] = useState(String(currentOrderPageNumber + 1));

    useEffect(() => {
        setPageInputValue(String(currentOrderPageNumber + 1));
    }, [currentOrderPageNumber]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            const pageNumber = parseInt(pageInputValue, 10);
            if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= countOfPages) {
                onPickerValueChange(pageNumber);
                setPageInputValue(String(pageNumber));
            } else {
                setPageInputValue(String(currentOrderPageNumber + 1));
            }
        }
    };

    const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPageInputValue(e.target.value);
    };

    const pagesDataSource = useArrayDataSource(
        {
            items: Array.from({ length: countOfPages }).map((_, index) => index + 1),
            getId: (item) => item
        },
        []
    );

    const updateCurrentPage = useCallback(
        (pageOrderNumber: number) => {
            onCurrentPageChange(pageNumbers[pageOrderNumber], pageOrderNumber);
            onPageChange(pageOrderNumber);
        },
        [onCurrentPageChange, onPageChange, pageNumbers]
    );

    const onPickerValueChange = useCallback(
        (selectedPageNumber: number) => {
            updateCurrentPage(selectedPageNumber - 1);
        },
        [updateCurrentPage]
    );

    const handleGoNext = useCallback(() => {
        updateCurrentPage(isLastPage ? countOfPages - 1 : currentOrderPageNumber + 1);
    }, [updateCurrentPage, isLastPage, countOfPages, currentOrderPageNumber]);

    const handleGoPrev = useCallback(() => {
        updateCurrentPage(isFirstPage ? 0 : currentOrderPageNumber - 1);
    }, [isFirstPage, currentOrderPageNumber, updateCurrentPage]);

    return (
        <>
            <FlexRow cx={styles['goto-page-selector']}>
                <span>Current page</span>
                <PickerInput
                    minBodyWidth={52}
                    size="24"
                    dataSource={pagesDataSource}
                    value={currentOrderPageNumber + 1}
                    onValueChange={onPickerValueChange}
                    getName={(item) => String(item)}
                    selectionMode="single"
                    disableClear={true}
                    searchPosition="input"
                    valueType="id"
                    rawProps={{
                        input: {
                            onChange: handlePageInputChange,
                            onKeyDown: handleKeyDown
                        }
                    }}
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
            <DocumentScale scale={scale} onChange={onScaleChange} />
        </>
    );
};
