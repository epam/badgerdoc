import React, { FC } from 'react';
import { useArrayDataSource } from '@epam/uui';
import { CategoryDataAttribute } from '../../../api/typings';

import { FlexRow, FlexCell, IconButton, PickerInput, TextInput, Text } from '@epam/loveship';
import { ReactComponent as AddIcon } from '@epam/assets/icons/common/action-add-18.svg';
import { ReactComponent as ClearIcon } from '@epam/assets/icons/common/content-clear-12.svg';

type CategoriesDataAttributesProps = {
    dataAttributes: Array<CategoryDataAttribute>;
    addDataAtt(): void;
    onNameDataAttChange(value: string, index: number): void;
    onTypeDataAttChange(value: string, index: number): void;
    onDataAttDelete(index: number): void;
};

const dataAttributesTypes = [
    {
        id: 'text',
        type: 'text'
    },
    {
        id: 'molecule',
        type: 'molecule'
    },
    {
        id: 'latex',
        type: 'latex'
    },
    {
        id: 'taxonomy',
        type: 'taxonomy'
    }
];

export const CategoriesDataAttributes: FC<CategoriesDataAttributesProps> = ({
    dataAttributes,
    addDataAtt,
    onNameDataAttChange,
    onTypeDataAttChange,
    onDataAttDelete
}) => {
    const attributesDataSource = useArrayDataSource(
        {
            items: dataAttributesTypes
        },
        []
    );

    return (
        <>
            <FlexRow padding="24">
                <IconButton icon={AddIcon} onClick={addDataAtt} />
                <Text>Add new attribute</Text>
            </FlexRow>
            {dataAttributes.map((el, index) => {
                return (
                    <div key={index}>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1.5}>
                                <TextInput
                                    value={el.name}
                                    onValueChange={(value: string) => {
                                        onNameDataAttChange(value, index);
                                    }}
                                    placeholder="Attribute name"
                                />
                            </FlexCell>
                            <FlexCell grow={1}>
                                <PickerInput
                                    dataSource={attributesDataSource}
                                    value={el.type}
                                    onValueChange={(value: string) => {
                                        onTypeDataAttChange(value, index);
                                    }}
                                    getName={(item) => item.type}
                                    selectionMode="single"
                                    valueType={'id'}
                                    placeholder="Select the type"
                                />
                            </FlexCell>
                            <IconButton icon={ClearIcon} onClick={() => onDataAttDelete(index)} />
                        </FlexRow>
                    </div>
                );
            })}
        </>
    );
};
