// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import { PickerInput, LabeledInput, TextInput, Button } from '@epam/loveship';
import { IFormApi, useArrayDataSource } from '@epam/uui';
import { useModelById } from 'api/hooks/models';
import { Model, Basement, SupportedArgs } from 'api/typings';
import React, { FC, useState, useEffect } from 'react';
import { StepValues } from './edit-step';
import styles from './edit-step.module.scss';

type FormProps = IFormApi<StepValues> & {
    models: Model[];
    stepCategories: { id: string; name: string }[] | undefined;
    basements: Basement[] | undefined;
    saveText: string;
};
type ModelVersions = {
    id: number;
    name: string;
    latest: boolean;
};
export const StepFormFields: FC<FormProps> = ({
    lens,
    save,
    models,
    stepCategories,
    basements,
    saveText
}) => {
    const modelId: string | undefined = lens.prop('model').get();

    const modelVer: number | undefined = lens.prop('version').get();

    const { data: model, refetch } = useModelById({ modelId, modelVer }, { enabled: false });

    const [supportedArgs, setSupportedArgs] = useState<SupportedArgs[]>([]);

    const modelsDataSourceUniq = useArrayDataSource<Model, string, any>(
        {
            items: models.filter(
                (value, index, self) =>
                    index === self.findIndex((t) => t.id === value.id && t.name === value.name)
            )
        },
        []
    );
    useEffect(() => {
        if (modelId) refetch();
    }, [modelId, modelVer]);
    useEffect(() => {
        modelId ?? lens.prop('version').toProps().onValueChange(modelId);
    }, [modelId]);
    const useModelVersionFilter = () => {
        let modelsFiltered = models.filter((model) => model.id === modelId);
        return modelsFiltered
            ? modelsFiltered.map(
                  (model) =>
                      ({
                          id: model.version,
                          name: model.id,
                          latest: model.latest
                      } as ModelVersions)
              )
            : [];
    };

    const modelVersionsDataSource = useArrayDataSource<ModelVersions, number, any>(
        {
            items: useModelVersionFilter()
        },
        [models, modelId]
    );

    useEffect(() => {
        if (!basements || !model) return;

        const basement = basements.find((basement) => basement.id === model.basement);

        const supArgs = basement?.supported_args ?? [];

        setSupportedArgs(supArgs);
    }, [model, basements]);

    const categoriesDataSource = useArrayDataSource(
        {
            items: stepCategories ?? []
        },
        [stepCategories]
    );

    return (
        <>
            <LabeledInput cx={`m-t-15`} label="Models" {...lens.prop('model').toProps()}>
                <PickerInput
                    {...lens.prop('model').toProps()}
                    dataSource={modelsDataSourceUniq}
                    getName={(item) => item?.id ?? ''}
                    entityName="Categories name"
                    selectionMode="single"
                    valueType={'id'}
                    sorting={{ field: 'id', direction: 'asc' }}
                    placeholder="Select Model"
                />
            </LabeledInput>
            <LabeledInput cx={`m-t-15`} label="Versions" {...lens.prop('version').toProps()}>
                <PickerInput
                    {...lens.prop('version').toProps()}
                    dataSource={modelVersionsDataSource}
                    getName={(item) => {
                        if (item.id) return `version-${item.id}${item.latest ? '(latest)' : ''}`;
                        return '';
                    }}
                    entityName="Versions"
                    selectionMode="single"
                    valueType={'id'}
                    sorting={{ field: 'id', direction: 'asc' }}
                    filter={{ name: modelId }}
                    placeholder="Select version"
                    isRequired={true}
                />
            </LabeledInput>
            {stepCategories?.length ? (
                <>
                    <LabeledInput
                        cx={`m-t-15`}
                        label="Categories"
                        {...lens.prop('categories').toProps()}
                    >
                        <PickerInput
                            {...lens.prop('categories').toProps()}
                            dataSource={categoriesDataSource}
                            getName={(item) => item.name ?? ''}
                            entityName="Categories name"
                            selectionMode="multi"
                            valueType={'id'}
                            sorting={{ field: 'name', direction: 'asc' }}
                            placeholder="Select Categories"
                            editMode="modal"
                        />
                    </LabeledInput>
                </>
            ) : null}
            {supportedArgs.map((supArg) => (
                <LabeledInput
                    key={supArg.name}
                    cx={`m-t-15`}
                    label={supArg.name}
                    {...lens.prop('args').prop(supArg.name).toProps()}
                >
                    <TextInput {...lens.prop('args').prop(supArg.name).toProps()} />
                </LabeledInput>
            ))}
            <Button cx={styles.button} onClick={save} caption={saveText} />
        </>
    );
};
