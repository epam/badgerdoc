// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { ReactElement } from 'react';
import { Router } from 'react-router-dom';
import { createBrowserHistory } from 'history';

const history = createBrowserHistory();

const withRouter = (testComponent: ReactElement) => (
    <Router history={history}>{testComponent}</Router>
);

export default withRouter;
