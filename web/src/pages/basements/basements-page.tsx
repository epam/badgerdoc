// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { useCallback, useState } from 'react';
import { Switch, Route, useRouteMatch, Redirect, useHistory } from 'react-router-dom';
import { svc } from '../../services';
import { INotification } from '@epam/uui';
import { SuccessNotification, Text } from '@epam/loveship';
import { BasementsTableConnector } from 'connectors/basements-table-connector';
import AddBasementConnector from '../../connectors/add-basement-connector/add-basement-connector';
import { Basement } from 'api/typings';

const BasementsPage = () => {
    const history = useHistory();
    const [popup, setPopup] = useState<{
        show: boolean;
        basement?: Basement;
    }>({
        show: false,
        basement: undefined
    });
    const { path } = useRouteMatch();

    const handleAddBasement = () => {
        history.push(`${path}/add`);
    };
    const handleBasementAdded = () => {
        history.push(`${path}`);
    };
    const handleNameClick = (basement?: Basement) => {
        setPopup({
            show: true,
            basement
        });
    };
    const handlePopupClose = () => {
        setPopup({
            show: false,
            basement: undefined
        });
    };

    const handleSuccess = useCallback(() => {
        svc.uuiNotifications.show(
            (props: INotification) => (
                <SuccessNotification {...props}>
                    <Text>Basement created successfully!</Text>
                </SuccessNotification>
            ),
            { duration: 2 }
        );
        handleBasementAdded();
    }, [handleBasementAdded]);
    return (
        <Switch>
            <Route exact path={path}>
                <BasementsTableConnector
                    onRowClick={handleNameClick}
                    onAddModel={handleAddBasement}
                    popup={popup}
                    onPopupClose={handlePopupClose}
                />
            </Route>
            <Route path={`${path}/add`}>
                <AddBasementConnector onBasementAdded={handleSuccess} />
            </Route>
            <Redirect to={path} />
        </Switch>
    );
};

export default React.memo(BasementsPage);
