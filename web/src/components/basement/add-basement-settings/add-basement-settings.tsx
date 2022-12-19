import React, { FC, useEffect, useState } from 'react';
import { LabeledInput, TextInput, Checkbox, Button } from '@epam/loveship';
import { Form, ILens } from '@epam/uui';
import styles from './add-basement-settings.module.scss';
import { Basement, SupportedArgs } from '../../../api/typings';
import BasementArgument from '../basement-argument/basement-argument';
import { ReactComponent as PlusIcon } from '@epam/assets/icons/common/content-plus-18.svg';

export type AddBasementSettingsProps = {
    lens: ILens<Basement>;
};

const AddBasementSettings: FC<AddBasementSettingsProps> = ({ lens }) => {
    const [args, setArgs] = useState<SupportedArgs[]>(lens.prop('supported_args').get());

    useEffect(() => {
        lens.prop('supported_args').set(args);
    }, [args]);

    const handleArgAdd = () => {
        setArgs([...args, { name: '', type: '' }]);
    };

    const handleArgChange = (index: number, field: string, value: string) => {
        const newArray = args.map((el, ind) => {
            if (ind === index) {
                return {
                    ...el,
                    [field]: value
                };
            }
            return el;
        });
        setArgs(newArray);
    };

    const handleArgDelete = (name: string) => {
        const newArray = args.filter((el) => el.name !== name);
        setArgs(newArray);
    };
    return (
        <div className={`flex flex-col form-wrapper`}>
            <h2 className="m-b-15">Basement settings</h2>
            <LabeledInput label="Basement ID" {...lens.prop('id').toProps()} cx="m-t-15" isRequired>
                <TextInput {...lens.prop('id').toProps()} cx="c-m-t-5" placeholder="Basement ID" />
            </LabeledInput>
            <LabeledInput
                label="Basement name"
                {...lens.prop('name').toProps()}
                cx="m-t-15"
                isRequired
            >
                <TextInput
                    {...lens.prop('name').toProps()}
                    cx="c-m-t-5"
                    placeholder="Basement name"
                />
            </LabeledInput>
            <LabeledInput {...lens.prop('name').toProps()} cx="m-t-15">
                <Checkbox {...lens.prop('gpu_support').toProps()} cx="m-t-5" label="GPU Support" />
            </LabeledInput>
            <h4 className="m-t-15">Supported arguments</h4>
            {args.map((el, index) => {
                return (
                    <Form<SupportedArgs>
                        key={index}
                        renderForm={({ lens }) => (
                            <BasementArgument
                                lens={lens}
                                deleteArgument={handleArgDelete}
                                handleChange={(field: string, value: string) =>
                                    handleArgChange(index, field, value)
                                }
                            />
                        )}
                        onSave={() => {
                            return new Promise<void>(() => {});
                        }}
                        value={{ ...lens.prop('supported_args').get()[index] }}
                    />
                );
            })}
            <Button
                icon={PlusIcon}
                cx={`m-t-15 ${styles.add}`}
                fill="light"
                caption="Add argument"
                onClick={handleArgAdd}
            />
        </div>
    );
};

export default AddBasementSettings;
