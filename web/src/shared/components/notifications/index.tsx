import React, { ReactNode, useMemo } from 'react';

import { ErrorNotification, SuccessNotification } from '@epam/loveship';
import { INotification, useUuiContext } from '@epam/uui';

export const useNotifications = () => {
    const { uuiNotifications } = useUuiContext();

    const notifySuccess = async (template: ReactNode, duration = 3) => {
        return uuiNotifications
            .show(
                (props: INotification) => (
                    <SuccessNotification {...props}>{template}</SuccessNotification>
                ),
                { duration }
            )
            .catch(() => null);
    };

    const notifyError = async (template: ReactNode, duration = 5) => {
        return uuiNotifications
            .show(
                (props: INotification) => (
                    <ErrorNotification {...props}>{template}</ErrorNotification>
                ),
                { duration }
            )
            .catch(() => null);
    };

    return useMemo(() => ({ notifySuccess, notifyError }), []);
};
