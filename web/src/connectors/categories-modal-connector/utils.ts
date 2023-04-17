import { Metadata } from '@epam/uui';
import { TFormValues } from './types';
import { Category } from 'api/typings';

export const getFormSchema = (formValues: TFormValues): Metadata<TFormValues> => ({
    props: {
        name: {
            isRequired: true
        },
        color: {
            isRequired: true
        },
        categoryId: {
            isRequired: true
        },
        parentId: {
            isRequired: formValues.withParentLabel,
            isDisabled: !formValues.withParentLabel
        },
        dataAttributes: {
            validators: [
                (dataAttributes) => [
                    dataAttributes.some(
                        ({ name, type }) => name === '' || type === '' || type === null
                    )
                ]
            ]
        }
    }
});

export const getDefaultValues = (category: Category | undefined) => {
    const {
        name,
        type,
        metadata,
        parent = null,
        data_attributes: dataAttributes = []
    } = category || {};

    return {
        categoryId: '',
        name: name ?? '',
        parentId: parent,
        type: type ?? 'box',
        withParentLabel: !parent,
        color: metadata?.color ?? '',
        dataAttributes: dataAttributes ?? []
    };
};
