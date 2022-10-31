import React, { ReactNode, useMemo } from 'react';
import { ErrorNotification, SuccessNotification } from '@epam/loveship';
import { INotification } from '@epam/uui';
import { noop } from 'lodash';
import { svc } from 'services';

export const useNotifications = () => {
    const notifySuccess = (template: ReactNode, duration = 3) => {
        return svc.uuiNotifications
            .show(
                (props: INotification) => (
                    <SuccessNotification {...props}>{template}</SuccessNotification>
                ),
                { duration }
            )
            .then(noop)
            .catch(noop);
    };

    const notifyError = (template: ReactNode) => {
        return svc.uuiNotifications
            .show(
                (props: INotification) => (
                    <ErrorNotification {...props}>{template}</ErrorNotification>
                ),
                { duration: 5 }
            )
            .then(noop)
            .catch(noop);
    };

    return useMemo(() => ({ notifySuccess, notifyError }), []);
};
