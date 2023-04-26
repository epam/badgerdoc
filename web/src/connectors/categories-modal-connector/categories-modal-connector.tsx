import React, { FC } from 'react';
import { useArrayDataSource } from '@epam/uui';
import {
    Button,
    Checkbox,
    FlexCell,
    FlexRow,
    FlexSpacer,
    LabeledInput,
    ModalBlocker,
    ModalFooter,
    ModalHeader,
    ModalWindow,
    Panel,
    PickerInput,
    ScrollBars,
    Text,
    TextInput,
    useForm
} from '@epam/loveship';
import { CategoriesColorPicker } from '../../components/categories/categories-color-picker/categories-color-picker';
import { CategoriesDataAttributes } from '../../components/categories/categories-data-attributes/categories-data-attributes';
import {
    categoriesFetcher,
    useAddCategoriesMutation,
    useCategories,
    useUpdateCategoriesMutation
} from '../../api/hooks/categories';
import { Category, CategoryType, categoryTypes, QueryHookParamsType } from '../../api/typings';
import { usePageTable } from '../../shared';
import { useNotifications } from '../../shared/components/notifications';
import { useEntity } from '../../shared/hooks/use-entity';
import { getError } from 'shared/helpers/get-error';

import { IProps, TCategoryOption, TFormValues } from './types';
import { getDefaultValues, getFormSchema } from './utils';

import styles from './styles.module.scss';

export const ModalWithDisabledClickOutsideAndCross: FC<IProps> = ({
    categoryValue,
    abort: onClose,
    ...props
}) => {
    const {
        sortConfig,
        pageConfig: { page, pageSize }
    } = usePageTable<Category>('name');
    const { notifyError, notifySuccess } = useNotifications();
    const { dataSource: categoriesDataSource } = useEntity<Category, string>(categoriesFetcher);
    const { refetch: refetchCategory } = useCategories(
        { page, size: pageSize, sortConfig } as QueryHookParamsType<Category>,
        {}
    );
    const categoryTypeDataSource = useArrayDataSource<TCategoryOption, CategoryType, unknown>(
        {
            items: categoryTypes.map((el) => ({ id: el, name: el }))
        },
        []
    );

    const addCategoryMutation = useAddCategoriesMutation();
    const updateCategoryMutation = useUpdateCategoriesMutation();

    const updateCategory = async (categoryId: string, formValues: TFormValues) => {
        await updateCategoryMutation.mutateAsync({
            id: categoryId,
            name: formValues.name,
            metadata: { color: formValues.color },
            type: formValues.type,
            parent: formValues.parentId,
            data_attributes: formValues.dataAttributes
        });
        notifySuccess(<Text>The category was updated successfully</Text>);
    };

    const addCategory = async (formValues: TFormValues) => {
        await addCategoryMutation.mutateAsync({
            id: formValues.categoryId,
            name: formValues.name,
            metadata: { color: formValues.color },
            type: formValues.type,
            parent: formValues.parentId,
            data_attributes: formValues.dataAttributes
        });
        notifySuccess(<Text>The category was successfully added</Text>);
    };

    const saveCategory = async (formValues: TFormValues) => {
        try {
            if (categoryValue?.id) {
                await updateCategory(categoryValue.id, formValues);
            } else {
                await addCategory(formValues);
            }

            await refetchCategory();
            onClose();
        } catch (err: any) {
            notifyError(<Text>{getError(err)}</Text>);
        }
    };

    const { lens, save } = useForm<TFormValues>({
        onSave: saveCategory,
        getMetadata: getFormSchema,
        value: getDefaultValues(categoryValue)
    });

    return (
        <ModalBlocker disallowClickOutside blockerShadow="dark" {...props} abort={onClose}>
            <ModalWindow>
                <Panel background="white">
                    <ModalHeader title="Add new category" />
                    <ScrollBars hasTopShadow hasBottomShadow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Category Name" isRequired>
                                    <TextInput {...lens.prop('name').toProps()} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput isRequired label="Category Id">
                                    <TextInput {...lens.prop('categoryId').toProps()} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput isRequired label="Color">
                                    <CategoriesColorPicker {...lens.prop('color').toProps()} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Category Type">
                                    <PickerInput<TCategoryOption, CategoryType>
                                        {...lens.prop('type').toProps()}
                                        disableClear
                                        valueType="id"
                                        minBodyWidth={100}
                                        selectionMode="single"
                                        getName={(item) => item.name}
                                        dataSource={categoryTypeDataSource}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <Checkbox
                                    {...lens.prop('withParentLabel').toProps()}
                                    label="Parent label"
                                    cx={styles['activate-checkbox-parent']}
                                />
                                <PickerInput
                                    {...lens.prop('parentId').toProps()}
                                    valueType="id"
                                    minBodyWidth={100}
                                    disableClear={true}
                                    selectionMode="single"
                                    dataSource={categoriesDataSource}
                                    getName={(item) => item?.name ?? 'test'}
                                />
                            </FlexCell>
                        </FlexRow>
                        <CategoriesDataAttributes {...lens.prop('dataAttributes').toProps()} />
                    </ScrollBars>
                    <ModalFooter>
                        <FlexSpacer />
                        <Button fill="white" caption="Cancel" onClick={onClose} />
                        <Button onClick={save} caption={categoryValue ? 'Update' : 'Save'} />
                    </ModalFooter>
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
