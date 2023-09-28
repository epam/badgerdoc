// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { Panel, PickerInput } from '@epam/loveship';
import { LazyDataSource } from '@epam/uui';

import styles from './preprocessor-picker.module.scss';
import { Model } from 'api/typings';

type PreprocessorPickerProps = {
    onPreprocessorSelect(preprocessor: string): void;
    dataSource: LazyDataSource<Model, string>;
    showTitle?: boolean;
    preprocessor: string | undefined;
};

export const PreprocessorPicker: FC<PreprocessorPickerProps> = ({
    onPreprocessorSelect,
    dataSource,
    showTitle,
    preprocessor
}) => {
    return (
        <Panel cx={styles['preprocessor-picker']}>
            {showTitle ? <h4>Preprocessors</h4> : null}
            <PickerInput<Model, string | undefined>
                dataSource={dataSource}
                value={preprocessor}
                onValueChange={onPreprocessorSelect}
                entityName="preprocessor"
                selectionMode="single"
                valueType="id"
                searchPosition="body"
            />
        </Panel>
    );
};
