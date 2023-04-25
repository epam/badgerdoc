import React, { FC, useEffect } from 'react';

import { Basement, Category, Model } from 'api/typings';

import CategoriesPicker from 'shared/components/categories-picker/categories-picker';
import BasementPicker from '../basement-picker/basement-picker';
import ModelPicker from '../model-picker/model-picker';
import { ModelValues } from '../model.models';

import { FlexRow, LabeledInput, Spinner, TextInput } from '@epam/loveship';
import { ILens } from '@epam/uui';

export type AddModelSettingsProps = {
    categories: Category[] | undefined;
    basements: Basement[] | undefined;
    models: Model[] | undefined;
    lens: ILens<ModelValues>;
};

export const AddModelSettings: FC<AddModelSettingsProps> = ({
    lens,
    categories,
    basements,
    models
}) => {
    if (!basements) return <Spinner color="sky" />;

    useEffect(() => {
        const baseModel = lens.prop('baseModel').toProps().value;

        if (baseModel) {
            const newCategories = categories?.filter((el) =>
                baseModel.categories?.includes(el.name)
            );
            const newBasement = basements?.find((el) => el.id === baseModel.basement);
            const newModel = {
                categories: newCategories,
                basement: newBasement,
                configuration_path_file: baseModel.configuration_path?.file,
                configuration_path_bucket: baseModel.configuration_path?.bucket,
                data_path_file: baseModel.data_path?.file,
                data_path_bucket: baseModel.data_path?.bucket,
                score: `${baseModel.score}` || undefined,
                type: baseModel.type || undefined,
                training_id: baseModel.training_id || undefined,
                baseModel,
                name: baseModel.name,
                id: baseModel.id,
                version: baseModel.version,
                jobs: undefined
            };
            lens.toProps().value = newModel;
            lens.set(newModel);
        }
    }, [lens.prop('baseModel').toProps().value?.name]);

    return (
        <div className={`flex flex-col form-wrapper`}>
            <h2 className="m-b-15">Model Settings</h2>
            <ModelPicker lens={lens} models={models} />
            <LabeledInput label="Model ID" {...lens.prop('id').toProps()} cx="m-t-15" isRequired>
                <TextInput {...lens.prop('id').toProps()} cx="c-m-t-5" placeholder="Model id" />
            </LabeledInput>
            <LabeledInput
                label="Model Name"
                {...lens.prop('name').toProps()}
                cx="m-t-15"
                isRequired
            >
                <TextInput {...lens.prop('name').toProps()} cx="c-m-t-5" placeholder="Model name" />
            </LabeledInput>
            <CategoriesPicker categories={categories} lens={lens} />
            <BasementPicker basements={basements} lens={lens} />
            <LabeledInput label="Model Type" {...lens.prop('type').toProps()} cx="m-t-15">
                <TextInput {...lens.prop('type').toProps()} cx="c-m-t-5" placeholder="Model type" />
            </LabeledInput>
            <FlexRow vPadding="12" cx="m-t-15">
                <LabeledInput label="Configuration path" />
            </FlexRow>
            <FlexRow padding="6">
                <LabeledInput label="File" {...lens.prop('configuration_path_file').toProps()}>
                    <TextInput
                        {...lens.prop('configuration_path_file').toProps()}
                        cx="c-m-t-5"
                        placeholder="File"
                    />
                </LabeledInput>
                <LabeledInput label="Bucket" {...lens.prop('configuration_path_bucket').toProps()}>
                    <TextInput
                        {...lens.prop('configuration_path_bucket').toProps()}
                        cx="c-m-t-5"
                        placeholder="Bucket"
                    />
                </LabeledInput>
            </FlexRow>
        </div>
    );
};

export default AddModelSettings;
