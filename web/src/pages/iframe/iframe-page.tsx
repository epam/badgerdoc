import React from 'react';
import { useLocation } from 'react-router-dom';

export const IframePage: React.FC = () => {
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const iframeUrl = searchParams.get('url') ?? '';
    const title = searchParams.get('name') ?? 'Iframe';

    return (
        <iframe
            src={iframeUrl}
            title={title}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
        />
    );
};
