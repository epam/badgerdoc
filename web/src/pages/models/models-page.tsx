// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { useCallback } from 'react';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router-dom';
import { ModelsTableConnector } from 'connectors/models-table-connector';
import FormModelConnector from '../../connectors/form-model-connector/form-model-connector';
import { svc } from '../../services';
import { ModelPage } from '../model/model-page';
import { getError } from '../../shared/helpers/get-error';
import { ActionTypeEnum } from '../../components/model/model.models';

import { INotification } from '@epam/uui';
import { ErrorNotification, SuccessNotification, Text } from '@epam/loveship';

const ModelsPage = () => {
    const history = useHistory();
    const { path } = useRouteMatch();

    const handleAddModel = () => {
        history.push(`${path}/add`);
    };
    const handleModelAdded = (id: number) => {
        history.push(`${path}/${id}`);
    };
    const handleNameClick = (id: string, version?: number) => {
        history.push(`${path}/${id}/${version ?? ''}`);
    };

    const handleError = useCallback((err: any) => {
        svc.uuiNotifications.show(
            (props: INotification) => (
                <ErrorNotification {...props}>
                    <Text>{getError(err)}</Text>
                </ErrorNotification>
            ),
            { duration: 2 }
        );
    }, []);

    const handleSuccess = useCallback(() => {
        svc.uuiNotifications.show(
            (props: INotification) => (
                <SuccessNotification {...props}>
                    <Text>Model submit successfully!</Text>
                </SuccessNotification>
            ),
            { duration: 2 }
        );
    }, [handleModelAdded]);

    return (
        <Switch>
            <Route exact path={path}>
                <ModelsTableConnector onRowClick={handleNameClick} onAddModel={handleAddModel} />
            </Route>
            <Route path={`${path}/add`}>
                <FormModelConnector
                    onModelSubmit={handleSuccess}
                    onError={handleError}
                    actionType={ActionTypeEnum.ADD}
                />
            </Route>
            <Route path={`${path}/:modelId/:modelVer/edit`}>
                <FormModelConnector
                    onModelSubmit={handleSuccess}
                    onError={handleError}
                    actionType={ActionTypeEnum.EDIT}
                />
            </Route>
            <Route path={`${path}/:modelId/:modelVer`}>
                <ModelPage />
            </Route>
            <Redirect to={path} />
        </Switch>
    );
};

export default React.memo(ModelsPage);
