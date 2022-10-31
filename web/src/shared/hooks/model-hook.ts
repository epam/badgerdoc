import { useMemo, useState } from 'react';
import { useArrayDataSource } from '@epam/uui';

export const useConfigView = () => {
    const [modelToBase, setModelToBase] = useState<string>('');
    const [basement, setBasement] = useState<string>('');
    const [category, setCategory] = useState<string>('');
    const [type, setType] = useState<string>('');
    const [valueID, setValueID] = useState<string>('');
    const [modelName, setModelName] = useState<string>('');

    const modelToBaseDataSource = useArrayDataSource(
        {
            items: []
        },
        []
    );
    return useMemo(
        () => [
            {
                labelName: 'Model to base on',
                type: 'pickerInput',
                isRequired: false,
                value: {
                    value: modelToBase,
                    valueChange: setModelToBase,
                    dataSource: modelToBaseDataSource
                }
            },
            {
                labelName: 'ID',
                type: 'textInput',
                isRequired: true,
                value: {
                    value: valueID,
                    valueChange: setValueID
                }
            },
            {
                labelName: 'Name',
                type: 'textInput',
                isRequired: true,
                value: {
                    value: modelName,
                    valueChange: setModelName
                }
            },
            {
                labelName: 'Basement',
                type: 'pickerInput',
                isRequired: true,
                value: {
                    value: basement,
                    valueChange: setBasement,
                    dataSource: modelToBaseDataSource
                }
            },
            {
                labelName: 'Categories',
                type: 'pickerInput',
                isRequired: true,
                value: {
                    value: category,
                    valueChange: setCategory,
                    dataSource: modelToBaseDataSource
                }
            },
            {
                labelName: 'Type',
                type: 'pickerInput',
                isRequired: false,
                value: {
                    value: type,
                    valueChange: setType,
                    dataSource: modelToBaseDataSource
                }
            }
        ],
        [modelToBase, valueID, modelName, basement, category, type]
    );
};
