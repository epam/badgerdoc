import React, { useCallback } from 'react';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router-dom';
import AddPipelineForm from 'components/pipeline/add-pipeline-form';
import { PipelineConnector } from 'connectors/pipeline-connector/pipeline-connector';
import PipelinesSidebar from 'components/pipeline/pipelines-sidebar/pipelines-sidebar';
import { Sidebar } from 'shared';
import { Pipeline } from 'api/typings';
import { ML_MENU_ITEMS } from '../../shared/contexts/current-user';
import { MultiSwitchMenu } from '../../shared/components/multi-switch-menu/MultiSwitchMenu';

export const PipelinesPage = () => {
    const history = useHistory();
    const { path } = useRouteMatch();

    const handlePipelineAddSuccess = useCallback(() => {
        history.push(`${path}`);
    }, []);

    const handleAddPipeline = useCallback(() => {
        history.push(`${path}/add`);
    }, []);

    const handleActivePipeline = (pipeline?: Pipeline) =>
        history.push(`${path}/${pipeline?.name ?? ''}`);

    return (
        <Switch>
            <Route path={`${path}/add`}>
                <AddPipelineForm onPipelineAddSuccess={handlePipelineAddSuccess} />
            </Route>

            <Route path={`${path}/:pipelineName?`}>
                {({ match }) => (
                    <Sidebar
                        title={
                            <MultiSwitchMenu
                                items={ML_MENU_ITEMS}
                                currentPath={history.location.pathname}
                            />
                        }
                        sideContent={
                            <PipelinesSidebar
                                onAddPipeline={handleAddPipeline}
                                onSelectPipeline={handleActivePipeline}
                            />
                        }
                        mainContent={
                            <PipelineConnector pipelineName={match?.params.pipelineName} />
                        }
                    />
                )}
            </Route>

            <Redirect to={path} />
        </Switch>
    );
};

export default React.memo(PipelinesPage);
