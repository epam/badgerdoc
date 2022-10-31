import { PickerInput, LabeledInput } from '@epam/loveship';
import { IEditable, useArrayDataSource } from '@epam/uui';

import { User } from 'api/typings';
import React, { FC } from 'react';
import { InfoIcon } from '../../../shared/components/info-icon/info-icon';

export type ChoiceProps = {
    inputProps: IEditable<User[]>;
    label: string;
    placeholder: string;
    infoCaption: string;
    infoDescription: string;
};

export type UsersProps = {
    users: User[] | undefined;
    typeProps: ChoiceProps[];
};
const UsersPicker: FC<UsersProps> = ({ users, typeProps }) => {
    const usersDataSource = useArrayDataSource(
        {
            items: users ?? []
        },
        [users]
    );
    return (
        <>
            {typeProps?.map((option, key) => {
                return (
                    <LabeledInput
                        key={key}
                        cx={`m-t-15`}
                        label={option.label}
                        {...option.inputProps}
                        isRequired
                    >
                        <div className="flex align-vert-center" style={{ width: '430px' }}>
                            <PickerInput
                                {...option.inputProps}
                                dataSource={usersDataSource}
                                getName={(item) => item?.username ?? ''}
                                selectionMode="multi"
                                valueType="entity"
                                sorting={{ field: 'username', direction: 'asc' }}
                                placeholder={option.placeholder}
                            />
                            <InfoIcon
                                title={option.infoCaption}
                                description={option.infoDescription}
                            />
                        </div>
                    </LabeledInput>
                );
            })}
        </>
    );
};

export default UsersPicker;
