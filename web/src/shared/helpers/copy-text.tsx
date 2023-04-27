import React from 'react';
import { SuccessNotification, Text } from '@epam/loveship';
import { INotification } from '@epam/uui';
import { svc } from 'services';

export const handleCopy = (e: React.MouseEvent<SVGSVGElement>, filename: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(filename).then(() => {
        svc.uuiNotifications.show(
            (props: INotification) => (
                <SuccessNotification {...props}>
                    <Text>Copied to clipboard! </Text>
                </SuccessNotification>
            ),
            { duration: 2 }
        );
    });
};
