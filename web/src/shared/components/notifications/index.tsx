import React, { ReactNode, useMemo } from 'react';
import {
    Text,
    HintNotification,
    ErrorNotification,
    SuccessNotification,
    WarningNotification
} from '@epam/loveship';
import { INotification, useUuiContext } from '@epam/uui';
import { svc } from 'services';

export enum NotificationTypes {
    hint = 'hint',
    error = 'error',
    success = 'success',
    warning = 'warning'
}

export const useNotifications = () => {
    const { uuiNotifications } = useUuiContext();

    const notifySuccess = (template: ReactNode, duration = 3) => {
        uuiNotifications
            .show(
                (props: INotification) => (
                    <SuccessNotification {...props}>{template}</SuccessNotification>
                ),
                { duration }
            )
            .catch(() => {});
    };

    const notifyError = (template: ReactNode, duration = 5) => {
        uuiNotifications
            .show(
                (props: INotification) => (
                    <ErrorNotification {...props}>{template}</ErrorNotification>
                ),
                { duration }
            )
            .catch(() => {});
    };

    return useMemo(() => ({ notifySuccess, notifyError }), []);
};

const getNotificationComponent = (type: NotificationTypes) => {
    switch (type) {
        case NotificationTypes.hint:
            return HintNotification;
        case NotificationTypes.error:
            return ErrorNotification;
        case NotificationTypes.warning:
            return WarningNotification;
        case NotificationTypes.success:
        default:
            return SuccessNotification;
    }
};

export const showNotification = ({
    text,
    type = NotificationTypes.success
}: {
    text: string;
    type: NotificationTypes;
}) => {
    const NotificationComponent = getNotificationComponent(type);

    svc.uuiNotifications
        .show((props) => (
            <NotificationComponent {...props}>
                <Text>{text}</Text>
            </NotificationComponent>
        ))
        .catch(() => {});
};

export const showError = (text: string) => {
    showNotification({ text, type: NotificationTypes.error });
};
