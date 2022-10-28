import React from 'react';
import { Panel, Text } from '@epam/loveship';
import { LoginConnector } from 'connectors/login-connector';
import { useNotifications } from 'shared/components/notifications';
import { ApiError } from 'api/api-error';

export const LoginPage = () => {
    const { notifySuccess, notifyError } = useNotifications();

    const onSuccess = () => {
        notifySuccess(<Text>You logged in successfully!</Text>, 2);

        setTimeout(() => {
            // here is hard reload to allow refetch current user in App
            window.location.href = '/';
        }, 300);
    };

    const onError = (error: ApiError) => {
        notifyError(
            <Panel>
                <Text font="sans-semibold" fontSize="16" color="fire">
                    {error.message}
                </Text>
                <Text>{error.summary}</Text>
            </Panel>
        );
    };

    return <LoginConnector onSuccess={onSuccess} onError={onError} />;
};
