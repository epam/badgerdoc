import { ILens } from '@epam/uui';
import { User, ValidationType } from 'api/typings';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import React, { FC } from 'react';
import UsersPicker from '../users-picker/users-picker';

type UsersPickersProps = {
    users: User[] | undefined;
    lens: ILens<JobValues>;
};
const UsersPickers: FC<UsersPickersProps> = ({ lens, users }) => {
    const lensValidationType: ValidationType = lens.prop('validationType').get();
    const owners = {
        label: 'Owners',
        inputProps: lens.prop('owners').toProps(),
        placeholder: 'Select Owners',
        infoCaption: 'Select Owners',
        infoDescription: 'Persons who have administrative rights for jobs.'
    };
    const validators = {
        label: 'Validators',
        inputProps: lens.prop('validators').toProps(),
        placeholder: 'Select Validators',
        infoCaption: 'Select Validators',
        infoDescription: 'Persons who will validate the annotation.'
    };
    const annotators = {
        label: 'Annotators',
        inputProps: lens.prop('annotators').toProps(),
        placeholder: 'Select Annotators',
        infoCaption: 'Select Annotators',
        infoDescription: 'Persons who will annotate documents.'
    };
    const annotatorsAndValidators = {
        label: 'Annotators and Validators',
        inputProps: lens.prop('annotators_validators').toProps(),
        placeholder: 'Select Annotators and Validators',
        infoCaption: 'Select Annotators & Validators',
        infoDescription:
            'Persons who will annotate documents and validate the annotation.(note: one person can be both a validator and an annotator at the same time, but a validator cannot validate his own annotation)'
    };

    const propMap = {
        cross: [owners, annotatorsAndValidators],
        hierarchical: [owners, annotators, validators],
        'validation only': [owners, validators],
        extensive_coverage: [owners, annotators, validators]
    };

    const typeProps = propMap[lensValidationType];
    return (
        <>
            <UsersPicker users={users} typeProps={typeProps} />
        </>
    );
};

export default UsersPickers;
