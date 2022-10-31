import React, { useCallback, useEffect, useState } from 'react';
import { Button, FlexRow } from '@epam/loveship';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router';
import { SHDashboardTableConnector } from '../../connectors/SH-dashboard-table-connector/SH-dashboard-table-connector';
import styles from './sh-dashboard.module.scss';

export function SkillHunterDashboardPage() {
    const { path } = useRouteMatch();
    const history = useHistory();
    const [filesIds, setFilesId] = useState<unknown>();

    useEffect(() => {
        setFilesId(history.location.state);
        history.location.state = undefined;
    }, [history.location.state]);

    const onJobWorkEnded = () => {
        setFilesId(null);
    };

    const handleTaskClick = (id: number) => {
        history.push(`dashboard/${id}`);
    };

    const handleUploadButtonClick = useCallback(() => {
        history.push(`${path}/upload`);
    }, []);

    return (
        <Switch>
            <Route exact path={path}>
                <div className={styles['main-container']}>
                    <FlexRow cx={styles['main-container-header']}>
                        <h1>My documents</h1>
                        <Button caption="Upload" onClick={handleUploadButtonClick} />
                    </FlexRow>
                    <SHDashboardTableConnector
                        onJobAdded={onJobWorkEnded}
                        filesIds={filesIds}
                        onRowClick={handleTaskClick}
                    />
                </div>
            </Route>
            <Redirect to={path} />
        </Switch>
    );
}
