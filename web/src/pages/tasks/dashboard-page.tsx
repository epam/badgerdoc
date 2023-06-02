import React from 'react';
import { TasksTableConnector } from 'connectors/tasks-table-connector/tasks-table-connector';
import styles from './dashboard-page.module.scss';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router';
import { BreadcrumbNavigation } from '../../shared/components/breadcrumb';
import { ANNOTATION_PAGE } from '../../shared/constants/general';
import { WarningText } from 'shared';

export function DashboardPage() {
    const { path } = useRouteMatch();
    const history = useHistory();

    const handleNameClick = (id: number) => {
        history.push(`${ANNOTATION_PAGE}/${id}`);
    };
    return (
        <Switch>
            <Route exact path={path}>
                <div className={styles['main-container']}>
                    <div className={styles['header']}>
                        <BreadcrumbNavigation breadcrumbs={[{ name: 'My Tasks' }]} />
                        <WarningText
                            warningText="Please note that this table shows only the tasks that are assigned to you"
                            fontsize="14"
                        />
                    </div>
                    <TasksTableConnector onRowClick={handleNameClick} />
                </div>
            </Route>
            <Redirect to={path} />
        </Switch>
    );
}
