import React from 'react';
import { Checkbox, PickerInput } from '@epam/loveship';
import styles from './categories-parent-selector.module.scss';
import { ArrayDataSource, LazyDataSource } from '@epam/uui';

type CategoriesParentSelectorProps = {
    setCheckBoxValue(status: boolean): void;
    checkBoxValue: boolean;
    setParentValue(color: string): void;
    parentValue: ArrayDataSource | null | any;
    categoriesDataSource: LazyDataSource;
};

export const CategoriesParentSelector: React.FC<CategoriesParentSelectorProps> = ({
    setCheckBoxValue,
    checkBoxValue,
    setParentValue,
    parentValue,
    categoriesDataSource
}) => {
    return (
        <>
            <Checkbox
                cx={styles['activate-checkbox-parent']}
                label="Parent label"
                value={checkBoxValue}
                onValueChange={setCheckBoxValue}
            />
            <PickerInput
                onValueChange={setParentValue}
                isDisabled={!checkBoxValue}
                getName={(item) => item?.name ?? 'test'}
                valueType="id"
                selectionMode="single"
                value={parentValue}
                minBodyWidth={100}
                disableClear={true}
                dataSource={categoriesDataSource}
            />
        </>
    );
};
