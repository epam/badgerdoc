import React, { FC } from 'react';
import { Report, User } from 'api/typings';
import { ILens } from '@epam/uui';
import UsersPicker, { ChoiceProps } from 'components/job/users-picker/users-picker';
import { DatePicker, LabeledInput } from '@epam/loveship';
import styles from './retrieve-reports-list.module.scss';

export type RetrieveReportsListProps = {
    lens: ILens<Report>;
    users: User[] | undefined;
};

const RetrieveReportsList: FC<RetrieveReportsListProps> = ({ lens, users }) => {
    const typeProps: ChoiceProps[] = [
        {
            label: 'User',
            inputProps: lens.prop('users').toProps(),
            placeholder: 'Select user',
            infoCaption: 'Select user',
            infoDescription: 'Person for which we want to retrieve reports list'
        }
    ];

    return (
        <div className={`${styles['form-wrapper']} flex flex-col form-wrapper m-b-5`}>
            <UsersPicker users={users} typeProps={typeProps} />
            <div className="flex">
                <LabeledInput
                    cx={`${styles['width-small']} m-t-15`}
                    label="From"
                    {...lens.prop('from').toProps()}
                >
                    <DatePicker {...lens.prop('from').toProps()} format="DD/MM/YYYY" />
                </LabeledInput>
                <LabeledInput
                    cx={`${styles['width-small']} m-t-15 m-l-20`}
                    label="To"
                    {...lens.prop('to').toProps()}
                >
                    <DatePicker {...lens.prop('to').toProps()} format="DD/MM/YYYY" />
                </LabeledInput>
            </div>
        </div>
    );
};

export default RetrieveReportsList;
