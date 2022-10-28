import React from 'react';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router-dom';
import { JobPage } from '../job/job-page';

import { JobsTableConnector } from 'connectors/jobs-table-connector';

import { AddJobPage } from './add-job-page';

const JobsPage = () => {
    const history = useHistory();
    const { path } = useRouteMatch();

    const handleAddJob = () => {
        history.push(`${path}/add`);
    };

    const handleNameClick = (id: number) => {
        history.push(`${path}/${id}`);
    };

    return (
        <Switch>
            <Route exact path={path}>
                <JobsTableConnector onRowClick={handleNameClick} onAddJob={handleAddJob} />
            </Route>
            <Route path={`${path}/add`} component={AddJobPage} />
            <Route component={JobPage} path={`${path}/:jobId`} />
            <Redirect to={path} />
        </Switch>
    );
};

export default React.memo(JobsPage);
