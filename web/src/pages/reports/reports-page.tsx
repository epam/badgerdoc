import { ReportsConnector } from 'connectors/reports-connector';
import React from 'react';

const ReportsPage = () => {
    return (
        <>
            <ReportsConnector />
        </>
    );
};

export default React.memo(ReportsPage);
