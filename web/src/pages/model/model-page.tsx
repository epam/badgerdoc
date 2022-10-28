import React from 'react';
import { useParams } from 'react-router-dom';
import { ModelDetailedViewConnector } from '../../connectors/model-detailed-view-connector/model-detailed-view-connector';

export function ModelPage() {
    const { modelId, modelVer } = useParams() as any;

    return (
        <div style={{ width: '100%' }}>
            <ModelDetailedViewConnector modelId={modelId} modelVer={modelVer} />
        </div>
    );
}
