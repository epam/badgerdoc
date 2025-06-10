import { Blocker, Panel, Text as ErrorText } from '@epam/loveship';
import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useNotifications } from 'shared/components/notifications';

import styles from './iframe-page.module.scss';

export const IframePage: React.FC = () => {
    const [isLoading, setIsLoading] = useState(true);
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const iframeUrl = searchParams.get('url') ?? '';
    const title = searchParams.get('name') ?? 'Iframe';

    // Clear the iframe source when the component unmounts to prevent memory leaks
    useEffect(() => {
        const iframeEl = iframeRef.current;

        return () => {
            if (iframeEl) {
                iframeEl.src = '';
            }
        };
    }, []);

    useEffect(() => {
        setIsLoading(true);
    }, [iframeUrl]);

    const { notifyError } = useNotifications();

    const handleError = (err: Error) => {
        setIsLoading(false);
        notifyError(
            <Panel>
                <ErrorText>{`Failed to load iframe: ${err.message}`}</ErrorText>
            </Panel>
        );
    };

    useEffect(() => {
        setIsLoading(true);
    }, [iframeUrl]);

    return (
        <div className={styles['iframe-page']}>
            <Blocker isEnabled={isLoading} />
            <iframe
                ref={iframeRef}
                src={iframeUrl}
                title={title}
                onLoad={() => setIsLoading(false)}
                onError={() => handleError(new Error('Unable to load iframe content'))}
            />
        </div>
    );
};
