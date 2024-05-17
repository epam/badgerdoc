// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { FC, useEffect, useState } from 'react';
import { FlexRow, IconButton, PickerInput, RadioInput, Text, Tooltip } from '@epam/loveship';
import { ReactComponent as InfoIcon } from '@epam/assets/icons/common/notification-info-outline-18.svg';
import { useArrayDataSource } from '@epam/uui';

import styles from './upload-wizard-preprocessor.module.scss';
import { Operators, SortingDirection } from '../../../api/typings';
import { usePagedPipelines } from '../../../api/hooks/pipelines';
import ModelInfo from '../model-info/model-info';

type RenderLabelProps = {
    title: string;
    models?: ModelsInfo[];
    comment?: string;
    info?: string;
};

type ModelsInfo = {
    model: string;
    ver: number;
};

export type UploadWizardPreprocessorResult = {
    preprocessor?: number | null;
    selectedLanguages: any[];
};

type UploadWizardPreprocessorProps = {
    onChange: (data: UploadWizardPreprocessorResult) => void;
};

const languages = [
    { id: 1, language: 'English' },
    { id: 2, language: 'French' },
    { id: 3, language: 'Russian' },
    { id: 4, language: 'Chinese' },
    { id: 5, language: 'Spanish' },
    { id: 6, language: 'Portuguese' }
];

const UploadWizardPreprocessor: FC<UploadWizardPreprocessorProps> = ({ onChange }) => {
    const [preprocessor, setPreprocessor] = useState<number | null>(null);
    const [selectedLanguages, setLanguages] = useState<any[]>([]);

    useEffect(() => {
        onChange({ preprocessor, selectedLanguages });
    }, [preprocessor, selectedLanguages]);

    const dataSource = useArrayDataSource(
        {
            items: languages
        },
        []
    );

    const { data: pipelines } = usePagedPipelines(
        {
            page: 1,
            size: 15,
            searchText: '',
            sortConfig: {
                field: 'name',
                direction: SortingDirection.ASC
            },
            filters: [
                {
                    field: 'type',
                    operator: Operators.EQ,
                    value: 'preprocessing'
                }
            ]
        },
        {
            refetchInterval: false
        }
    );

    useEffect(() => {
        setPreprocessor((pipelines?.data.length && pipelines?.data[0].id) || null);
    }, [pipelines]);
    const renderLabel = ({ title, models, comment, info }: RenderLabelProps) => {
        return (
            <div>
                <FlexRow spacing="12" alignItems="top" size="24">
                    <Text cx="p-b-5 p-t-0">{title}</Text>
                    {info && (
                        <Tooltip content={info}>
                            <IconButton icon={InfoIcon} />
                        </Tooltip>
                    )}
                </FlexRow>
                {comment && (
                    <Text cx="p-b-0 p-t-0" fontSize="12">
                        {comment}
                    </Text>
                )}
                {models && (
                    <FlexRow spacing="6">
                        {models?.map((el) => (
                            <ModelInfo id={el.model} key={el.model} ver={el.ver} />
                        ))}
                    </FlexRow>
                )}
            </div>
        );
    };
    return (
        <div className={`form-wrapper`}>
            <div className="form-group">
                <div className={styles.title}>Select preprocessor</div>
                <RadioInput
                    value={preprocessor === null}
                    onValueChange={() => setPreprocessor(null)}
                    renderLabel={() =>
                        renderLabel({
                            title: 'No need for preprocessor',
                            comment:
                                'There is no need to preprocess files  which consist only of pictures'
                        })
                    }
                />
            </div>
            {pipelines?.data?.map((el) => {
                return (
                    <div className="form-group" key={el.id}>
                        <RadioInput
                            cx="m-b-20"
                            value={preprocessor === el.id}
                            onValueChange={() => setPreprocessor(el.id)}
                            renderLabel={() =>
                                renderLabel({
                                    title: el.name,
                                    models: el.steps?.map((el) => ({
                                        model: el.model,
                                        ver: el.version!
                                    })),
                                    comment: el.description || '',
                                    info: el.summary
                                })
                            }
                        />
                    </div>
                );
            })}
            <div className="form-group">
                <div className={styles.title}>Select languages</div>
                <PickerInput
                    dataSource={dataSource}
                    selectionMode="multi"
                    value={selectedLanguages}
                    onValueChange={(value) => setLanguages(value)}
                    valueType={'id'}
                    getName={(item) => item?.language || ''}
                />
            </div>
        </div>
    );
};

export default UploadWizardPreprocessor;
