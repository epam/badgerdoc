import { Blocker, Panel, Text as ErrorText } from '@epam/loveship';
import React, { useEffect, useRef, useState } from 'react';
import { useNotifications } from 'shared/components/notifications';
import { getError } from 'shared/helpers/get-error';

import styles from './iframe-page.module.scss';

type IframePageProps = {
    src: string;
    title?: string;
};

export const IframePage: React.FC<IframePageProps> = ({ src, title = 'Iframe' }) => {
    const [isLoading, setIsLoading] = useState(true);
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const { notifyError } = useNotifications();

    useEffect(() => {
        setIsLoading(true);
    }, [src]);

    useEffect(() => {
        const iframeEl = iframeRef.current;
        return () => {
            if (iframeEl) {
                iframeEl.src = '';
            }
        };
    }, []);

    const handleError = (error: Error) => {
        setIsLoading(false);
        notifyError(
            <Panel>
                <ErrorText>{getError(error)}</ErrorText>
            </Panel>
        );
    };

    return (
        <div className={styles['iframe-page']}>
            <Blocker isEnabled={isLoading} />
            <iframe
                ref={iframeRef}
                src={src}
                title={title}
                onLoad={() => setIsLoading(false)}
                onError={() => handleError(new Error('Unable to load iframe content'))}
            />
        </div>
    );
};
