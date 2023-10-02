// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import React from 'react';
import { SuccessNotification, Text } from '@epam/loveship';
import { INotification } from '@epam/uui';
import { svc } from 'services';

const unsecuredCopyToClipboard = (filename: string) => {
    const textArea = document.createElement('textarea');
    textArea.value = filename;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        showCopied();
    } catch (err) {
        console.error('Unable to copy to clipboard', err);
    }
    document.body.removeChild(textArea);
};

const showCopied = () => {
    svc.uuiNotifications.show(
        (props: INotification) => (
            <SuccessNotification {...props}>
                <Text>Copied to clipboard! </Text>
            </SuccessNotification>
        ),
        { duration: 2 }
    );
};

export const handleCopy = (e: React.MouseEvent<SVGSVGElement>, filename: string) => {
    e.stopPropagation();
    if (window.isSecureContext && navigator.clipboard) {
        navigator.clipboard.writeText(filename).then(showCopied);
    } else {
        unsecuredCopyToClipboard(filename);
    }
};
