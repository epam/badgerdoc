import { useEffect } from 'react';
import { NotificationTypes, showNotification } from 'shared/components/notifications';

const notifyProcessing = () => {
    showNotification({
        type: NotificationTypes.hint,
        text: 'Your file is still processing. This may take a while'
    });
};

export const useNotifyProcessing = (isUploaded: boolean) => {
    useEffect(() => {
        let delay = 10000;
        let timeoutId: NodeJS.Timeout | null = null;
        let firstNotificationShown = false;

        const showNextNotification = () => {
            if (!isUploaded) return;

            if (!firstNotificationShown) {
                timeoutId = setTimeout(() => {
                    firstNotificationShown = true;
                    showNextNotification();
                }, delay);
            } else {
                notifyProcessing();

                delay *= 2;
                timeoutId = setTimeout(showNextNotification, delay);
            }
        };

        showNextNotification();

        return () => {
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
            }
        };
    }, [isUploaded]);
};
