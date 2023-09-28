// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { FC } from 'react';
import { useArrayDataSource } from '@epam/uui';
import { CategoryDataAttrType, CategoryDataAttribute } from '../../../api/typings';

import { FlexRow, FlexCell, IconButton, PickerInput, TextInput, Text } from '@epam/loveship';
import { ReactComponent as AddIcon } from '@epam/assets/icons/common/action-add-18.svg';
import { ReactComponent as ClearIcon } from '@epam/assets/icons/common/content-clear-12.svg';

type CategoriesDataAttributesProps = {
    value: Array<CategoryDataAttribute>;
    isInvalid?: boolean;
    onValueChange(value: Array<CategoryDataAttribute>): void;
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
    value,
    isInvalid,
    onValueChange
}) => {
    const attributesDataSource = useArrayDataSource(
        {
            items: dataAttributesTypes
        },
        []
    );

    const addDataAtt = () => {
        const newElem: CategoryDataAttribute = {
            name: '',
            type: ''
        };
        onValueChange([newElem, ...value]);
    };

    const onDataAttChange = (
        keyValue: CategoryDataAttrType | string,
        index: number,
        keyName: string
    ) => {
        const newDataArr = [...value];
        newDataArr[index] = {
            ...newDataArr[index],
            [keyName]: keyValue
        };

        onValueChange(newDataArr);
    };

    const onNameDataAttChange = (dataAttrName: string, index: number) => {
        onDataAttChange(dataAttrName, index, 'name');
    };

    const onTypeDataAttChange = (dataAttrType: CategoryDataAttrType, index: number) => {
        onDataAttChange(dataAttrType, index, 'type');
    };

    const onDataAttDelete = (index: number) => {
        onValueChange(value.filter((_, i) => i !== index));
    };

    return (
        <>
            <FlexRow padding="24">
                <IconButton icon={AddIcon} onClick={addDataAtt} />
                <Text>Add new attribute</Text>
            </FlexRow>
            {value.map((el, index) => (
                <div key={index}>
                    <FlexRow padding="24" vPadding="12">
                        <FlexCell grow={1.5}>
                            <TextInput
                                value={el.name}
                                placeholder="Attribute name"
                                isInvalid={!el.name && isInvalid}
                                onValueChange={(value: string) => {
                                    onNameDataAttChange(value, index);
                                }}
                            />
                        </FlexCell>
                        <FlexCell grow={1}>
                            <PickerInput
                                dataSource={attributesDataSource}
                                value={el.type}
                                onValueChange={(dataAttrType: CategoryDataAttrType) => {
                                    onTypeDataAttChange(dataAttrType, index);
                                }}
                                getName={(item) => item.type}
                                selectionMode="single"
                                valueType={'id'}
                                placeholder="Select the type"
                                isInvalid={!el.type && isInvalid}
                            />
                        </FlexCell>
                        <IconButton icon={ClearIcon} onClick={() => onDataAttDelete(index)} />
                    </FlexRow>
                </div>
            ))}
        </>
    );
};
