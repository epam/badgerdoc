// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import styles from './basement-argument.module.scss';
import { Button, LabeledInput, TextInput } from '@epam/loveship';
import { ILens } from '@epam/uui';
import { SupportedArgs } from 'api/typings';
import { ReactComponent as DeleteIcon } from '@epam/assets/icons/common/navigation-close_bold-18.svg';

type BasementArgumentProps = {
    lens: ILens<SupportedArgs>;
    deleteArgument: (arg: string) => void;
    handleChange: (field: string, value: string) => void;
};

const BasementArgument: FC<BasementArgumentProps> = ({ lens, deleteArgument, handleChange }) => {
    return (
        <div className={`${styles.container} flex flex-col`}>
            <div className={`${styles.content} flex justify-between`}>
                <LabeledInput label="Name" {...lens.prop('name').toProps()} cx="m-r-15" isRequired>
                    <TextInput
                        {...lens.prop('name').toProps()}
                        onValueChange={(newValue) => handleChange('name', newValue || '')}
                        cx="m-r-15"
                        placeholder="Argument name"
                    />
                </LabeledInput>
                <LabeledInput label="Type" {...lens.prop('type').toProps()} cx="m-r-15" isRequired>
                    <TextInput
                        {...lens.prop('type').toProps()}
                        onValueChange={(newValue) => handleChange('type', newValue || '')}
                        cx="c-m-t-5"
                        placeholder="Argument type"
                    />
                </LabeledInput>
                <Button
                    icon={DeleteIcon}
                    fill="light"
                    onClick={() => deleteArgument(lens.prop('name').get())}
                />
            </div>
        </div>
    );
};

export default BasementArgument;
