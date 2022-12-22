import React, { FC, useState } from 'react';
import { IModal, useArrayDataSource } from '@epam/uui';
import {
    Button,
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
    TextInput
} from '@epam/loveship';
import { CategoriesColorPicker } from '../../components/categories/categories-color-picker/categories-color-picker';
import { CategoriesDataAttributes } from '../../components/categories/categories-data-attributes/categories-data-attributes';
import {
    categoriesFetcher,
    useAddCategoriesMutation,
    useCategories,
    useUpdateCategoriesMutation
} from '../../api/hooks/categories';
import {
    Category,
    CategoryDataAttribute,
    CategoryDataAttrType,
    CategoryType,
    categoryTypes,
    QueryHookParamsType
} from '../../api/typings';
import { usePageTable } from '../../shared';
import { useNotifications } from '../../shared/components/notifications';
import { CategoriesParentSelector } from '../../components/categories/categories-parent-selector/categories-parent-selector';
import { useEntity } from '../../shared/hooks/use-entity';

export interface TaskValidationValues {
    categoryValue?: Category;
}
interface IProps extends IModal<TaskValidationValues> {
    categoryValue?: Category;
}

export const ModalWithDisabledClickOutsideAndCross: FC<IProps> = (props) => {
    const {
        name: nameProps = '',
        parent: parenProps = null,
        type: typeProps = null,
        metadata: { color: colorProps = '#000000' } = {},
        data_attributes: dataAttributesProps = []
    } = props?.categoryValue || {};
    const { pageConfig, sortConfig } = usePageTable<Category>('name');
    const [color, setColor] = useState(colorProps);
    const [checkBoxValue, setCheckBoxValue] = useState<boolean>(parenProps !== undefined);
    const [type, setType] = useState<CategoryType>(typeProps ?? 'box');
    const [categoryName, setCategoryName] = useState<string | undefined>(nameProps);
    const [categoryId, setCategoryId] = useState<string | undefined>(nameProps);
    const [parentValue, setParentValue] = useState<string | null>(parenProps);
    const { page, pageSize } = pageConfig;
    const { notifyError, notifySuccess } = useNotifications();
    const { data: categories, refetch: refetchCategory } = useCategories(
        { page, size: pageSize, sortConfig } as QueryHookParamsType<Category>,
        {}
    );
    const [dataAttributes, setDataAttributes] = useState(dataAttributesProps || []);

    const { dataSource } = useEntity<Category, Category>(categoriesFetcher);

    const categoryTypeDataSource = useArrayDataSource(
        {
            items: categoryTypes.map((el) => ({ id: el, name: el }))
        },
        []
    );

    const updateCategoryMutation = useUpdateCategoriesMutation();
    const addCategoryMutation = useAddCategoriesMutation();

    const updateCategory = async () => {
        try {
            await updateCategoryMutation.mutateAsync({
                id: props.categoryValue!.id,
                name: categoryName!,
                metadata: { color: color },
                type: type,
                parent: parentValue,
                data_attributes: dataAttributes
            });
            await refetchCategory();
            notifySuccess(<Text>The category was updated successfully</Text>);
        } catch (err: any) {
            notifyError(<Text>{err}</Text>);
        }
    };

    const addCategory = async () => {
        try {
            await addCategoryMutation.mutateAsync({
                id: categoryId!,
                name: categoryName!,
                metadata: { color: color },
                type: type,
                parent: parentValue
            });
            await refetchCategory();
            notifySuccess(<Text>The category was successfully added</Text>);
        } catch (err: any) {
            notifyError(<Text>{err}</Text>);
        }
    };

    const saveCategory = async () => {
        const findEmptyAtt = dataAttributes.filter(
            ({ name, type }) => name === '' || type === '' || type === null
        );

        if (categoryName?.length && color && !findEmptyAtt.length && categoryId?.length) {
            if (props.categoryValue) {
                await updateCategory();
            } else {
                await addCategory();
            }
            return true;
        }
        return false;
    };

    const addDataAtt = () => {
        const newElem: CategoryDataAttribute = {
            name: '',
            type: ''
        };
        setDataAttributes((prevState) => [newElem, ...prevState]);
    };

    const onDataAttChange = (
        value: CategoryDataAttrType | string,
        index: number,
        keyName: string
    ) => {
        const newDataArr = [...dataAttributes];
        newDataArr[index] = {
            ...newDataArr[index],
            [keyName]: value
        };

        setDataAttributes(newDataArr);
    };

    const onNameDataAttChange = (value: string, index: number) => {
        onDataAttChange(value, index, 'name');
    };

    const onTypeDataAttChange = (value: CategoryDataAttrType, index: number) => {
        onDataAttChange(value, index, 'type');
    };

    const onDataAttDelete = (index: number) => {
        setDataAttributes((prevState) => prevState.filter((_, i) => i !== index));
    };

    return (
        <ModalBlocker disallowClickOutside blockerShadow="dark" {...props}>
            <ModalWindow>
                <Panel background="white">
                    <ModalHeader title="Add new category" />
                    <ScrollBars hasTopShadow hasBottomShadow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Category Name">
                                    <TextInput
                                        value={categoryName}
                                        onValueChange={setCategoryName}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Category Id">
                                    <TextInput value={categoryId} onValueChange={setCategoryId} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Color">
                                    <CategoriesColorPicker
                                        defaultColor={color}
                                        selectedColor={(color) => {
                                            setColor(color);
                                        }}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Category Type">
                                    <PickerInput
                                        onValueChange={setType}
                                        getName={(item) => item.name}
                                        valueType="id"
                                        selectionMode="single"
                                        value={type}
                                        minBodyWidth={100}
                                        disableClear={true}
                                        dataSource={categoryTypeDataSource}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <CategoriesParentSelector
                                    setCheckBoxValue={setCheckBoxValue}
                                    checkBoxValue={checkBoxValue}
                                    setParentValue={setParentValue}
                                    parentValue={parentValue}
                                    categoriesDataSource={dataSource}
                                />
                            </FlexCell>
                        </FlexRow>

                        <CategoriesDataAttributes
                            dataAttributes={dataAttributes}
                            addDataAtt={addDataAtt}
                            onNameDataAttChange={onNameDataAttChange}
                            onTypeDataAttChange={onTypeDataAttChange}
                            onDataAttDelete={onDataAttDelete}
                        />
                    </ScrollBars>
                    <ModalFooter>
                        <FlexSpacer />
                        <Button fill="white" caption="Cancel" onClick={() => props.abort()} />
                        <Button
                            caption={props.categoryValue ? 'Update' : 'Save'}
                            onClick={async () => {
                                let success = await saveCategory();
                                success
                                    ? props.abort()
                                    : notifyError(<Text>{'Fill the form'}</Text>);
                            }}
                        />
                    </ModalFooter>
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
