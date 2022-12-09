import React, { useEffect } from 'react';

import {
    FlexCell,
    FlexRow,
    FlexSpacer,
    Button,
    LabeledInput,
    TextInput,
    Form
} from '@epam/loveship';

import { RenderFormProps } from '@epam/uui';
import { Paper } from 'shared';
import { Credentials, AuthResultRaw } from 'api/typings';
import { useAuthByCredsMutation, authWithSSO, useAuthBySSOMutation } from 'api/hooks/auth';
import noop from 'lodash/noop';
import { ApiError } from 'api/api-error';
import { setAuthDetails, setCurrentTenant } from 'shared/helpers/auth-tools';

interface LoginConnectorProps {
    onSuccess: () => void;
    onError: (error: ApiError) => void;
}

export const LoginConnector = ({ onSuccess = noop, onError = noop }: LoginConnectorProps) => {
    const { mutate, data, error } = useAuthByCredsMutation();
    const { mutate: mutateSSO, data: dataSSO, error: errorSSO } = useAuthBySSOMutation();

    useEffect(() => {
        if (location.hash) {
            const searchParams = new URLSearchParams(location.hash);
            const authRaw: AuthResultRaw = {
                access_token: searchParams.get('access_token') || '',
                expires_in: parseInt(searchParams.get('expires_in') || '0')
            };
            mutateSSO(authRaw);
        }
    }, []);

    useEffect(() => {
        const info = data || dataSSO;
        if (info) {
            setAuthDetails(info);
            setCurrentTenant(info.tenants[0]);
            onSuccess();
        }
    }, [data, dataSSO]);

    useEffect(() => {
        const err = errorSSO || error;

        if (err) {
            onError(err);
        }
    }, [error, errorSSO]);

    const renderForm = ({ lens, save }: RenderFormProps<Credentials>) => {
        const handleFormInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
            if (e.code === 'Enter') {
                save();
            }
        };

        return (
            <FlexCell width="100%">
                <FlexRow vPadding="12" alignItems="center">
                    <FlexCell grow={1}>
                        <Button caption="Login with SSO" fontSize="18" onClick={authWithSSO} />
                    </FlexCell>
                </FlexRow>
                <FlexRow vPadding="12" alignItems="center">
                    <FlexSpacer />
                    <span
                        style={{ fontSize: '18px', fontWeight: 'bold', textTransform: 'uppercase' }}
                    >
                        or
                    </span>
                    <FlexSpacer />
                </FlexRow>
                <FlexRow vPadding="12">
                    <FlexCell grow={1}>
                        <LabeledInput label="Username" {...lens.prop('username').toProps()}>
                            <TextInput
                                onKeyDown={handleFormInputKeyDown}
                                placeholder="Username"
                                {...lens.prop('username').toProps()}
                            />
                        </LabeledInput>
                    </FlexCell>
                </FlexRow>
                <FlexRow vPadding="12">
                    <FlexCell grow={1}>
                        <LabeledInput label="Password" {...lens.prop('password').toProps()}>
                            <TextInput
                                onKeyDown={handleFormInputKeyDown}
                                type="password"
                                placeholder="Password"
                                {...lens.prop('password').toProps()}
                            />
                        </LabeledInput>
                    </FlexCell>
                </FlexRow>
                <FlexRow vPadding="12">
                    <FlexSpacer />
                    <Button caption="Login" onClick={save} />
                </FlexRow>
            </FlexCell>
        );
    };

    return (
        <Paper centered width="500px" padding="25px">
            <Form
                value={{
                    username: '',
                    password: ''
                }}
                beforeLeave={async () => false}
                onSave={async (creds) => mutate(creds)}
                settingsKey="login-form"
                renderForm={renderForm}
            ></Form>
        </Paper>
    );
};
