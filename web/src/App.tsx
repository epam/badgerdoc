// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { Redirect, Route, Switch, useHistory } from 'react-router-dom';

import DocumentsPage from 'pages/documents/documents-page';
import PipelinesPage from 'pages/pipelines/pipelines-page';
import JobsPage from 'pages/jobs/jobs-page';
import { DashboardPage } from 'pages/tasks/dashboard-page';

import { AppHeader } from './app-header';
import css from './App.module.scss';
import { LoginPage } from 'pages/login/login-page';
import { User } from 'api/typings';
import { UserContextProvider } from 'shared/contexts/current-user';
import { useCurrentUser } from 'api/hooks/auth';
import TaskPage from 'pages/task/task-page';
import ModelsPage from './pages/models/models-page';
import BasementsPage from './pages/basements/basements-page';
import ReportsPage from 'pages/reports/reports-page';
import { SkillHunterDashboardPage } from './pages/SH-Dashboard/sh-dashboard';
import { setUpdateTokenInterval } from './shared/helpers/auth-tools';
import {
    ANNOTATION_PAGE,
    BASEMENTS_PAGE,
    DASHBOARD_PAGE,
    DOCUMENTS_PAGE,
    JOBS_PAGE,
    MODELS_PAGE,
    PIPELINES_PAGE,
    REPORTS_PAGE,
    IFRAME_PAGE,
    PLUGINS_PAGE
} from './shared/constants/general';
import { ProtectedRoute } from 'shared/components/protected-route';
import { CategoriesTableConnector } from './connectors/categories-table-connector';
import { IframePage } from 'pages/iframe/iframe-page';
import { PluginsTableConnector } from 'connectors/plugins-table-connector/plugins-table-connector';

export const App = () => {
    const history = useHistory();

    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const { data: user, isFetched } = useCurrentUser(history.location.pathname !== '/login');

    useEffect(() => {
        if (user && user.tenants) {
            user.id = user.sub;
            user.current_tenant = localStorage.getItem('tenant') ?? user.tenants[0];
            setCurrentUser(user);
        } else if (isFetched) {
            // if we fetched user but there is none, go to login to get jwt
            history.push('/login');
        }
    }, [user, isFetched]);

    setUpdateTokenInterval();

    return (
        <UserContextProvider currentUser={currentUser}>
            <div className={css.app}>
                <Route component={AppHeader} />
                <main className={css.main}>
                    <Switch>
                        <ProtectedRoute path={DOCUMENTS_PAGE} component={DocumentsPage} />
                        <ProtectedRoute path={PIPELINES_PAGE} component={PipelinesPage} />
                        <ProtectedRoute path={JOBS_PAGE} component={JobsPage} />
                        <Route path={DASHBOARD_PAGE} component={DashboardPage} />
                        <Route path="/login" component={LoginPage} />
                        <Route path="/tasks/:taskId" component={TaskPage} />
                        <Route path="/categories" component={CategoriesTableConnector} />
                        <Route path={MODELS_PAGE} component={ModelsPage} />
                        <Route path={BASEMENTS_PAGE} component={BasementsPage} />
                        <Route path={REPORTS_PAGE} component={ReportsPage} />
                        <Route path="/my documents" component={SkillHunterDashboardPage} />
                        <Route path={`${ANNOTATION_PAGE}/:taskId`} component={TaskPage} />
                        <Route path={PLUGINS_PAGE} component={PluginsTableConnector} />
                        <Route path={IFRAME_PAGE} component={IframePage} />
                        <Redirect to="/documents" />
                    </Switch>
                </main>
            </div>
        </UserContextProvider>
    );
};
