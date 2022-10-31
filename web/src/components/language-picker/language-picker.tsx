import React, { FC } from 'react';
import { Panel, PickerInput } from '@epam/loveship';
import { ArrayDataSource } from '@epam/uui';
import { Language } from 'api/typings';

import styles from './language-picker.module.scss';

type LanguagePickerProps = {
    onLanguageSelect(languages: string[]): void;
    dataSource: ArrayDataSource<Language>;
    showTitle?: boolean;
    isDisabled: boolean;
    value: string[];
};

export const LanguagePicker: FC<LanguagePickerProps> = ({
    onLanguageSelect,
    dataSource,
    showTitle,
    isDisabled,
    value
}) => {
    return (
        <Panel cx={styles['language-picker']}>
            {showTitle ? <h4>Language</h4> : null}
            <PickerInput
                dataSource={dataSource}
                value={value}
                onValueChange={onLanguageSelect}
                isDisabled={isDisabled}
                entityName="language"
                selectionMode="multi"
                valueType="id"
                searchPosition="body"
            />
        </Panel>
    );
};
