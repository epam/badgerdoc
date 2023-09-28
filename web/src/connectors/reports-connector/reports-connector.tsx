// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps, @typescript-eslint/no-redeclare */
import React, { FC, useCallback, useEffect, useState } from 'react';
import { useUsers } from 'api/hooks/users';
import { Report, SortingDirection } from 'api/typings';
import { useHistory } from 'react-router-dom';
import { MultiSwitchMenu } from 'shared/components/multi-switch-menu/MultiSwitchMenu';
import { ML_MENU_ITEMS } from 'shared/contexts/current-user';
import RetrieveReportsList from 'components/reports/retrieve-reports-list';
import { renderWizardButtons } from 'shared/components/wizard/wizard/wizard';
import { useDownloadTaskReport } from 'api/hooks/tasks';
import { useDownloadFile } from 'shared/hooks/use-download-file';
import { getError } from 'shared/helpers/get-error';

import { ErrorNotification, Panel, Text } from '@epam/loveship';
import { Form, INotification, Metadata, IFormApi, useUuiContext } from '@epam/uui';
import styles from './reports-connector.module.scss';

let initialValues: Report = {
    users: [],
    from: '',
    to: '',
    validationType: undefined
};

const timeAppendix = '00:00:00';

export const ReportsConnector: FC<{}> = () => {
    const finishButtonCaption = 'Download';
    const history = useHistory();
    const svc = useUuiContext();
    const [isLoading, setLoading] = useState(false);

    const users = useUsers(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'username', direction: SortingDirection.ASC }
        },
        {}
    );

    useEffect(() => {
        initialValues = { ...initialValues, users: users.data?.data };
    }, []);

    const handleError = useCallback((err) => {
        setLoading(false);

        svc.uuiNotifications.show(
            (props: INotification) => (
                <ErrorNotification {...props}>
                    <Text>{getError(err)}</Text>
                </ErrorNotification>
            ),
            { duration: 2 }
        );
    }, []);

    const { ref, url, download, name } = useDownloadFile({
        preDownloading: () => setLoading(true),
        postDownloading: () => setLoading(false),
        onError: (err) => handleError(err)
    });

    const renderForm = useCallback(
        ({ lens, save }: IFormApi<Report>) => {
            const values = users.data?.data;

            const formInvalid = isFormInvalid(lens);
            // temporary_disabled_rules
            /* eslint-disable jsx-a11y/anchor-has-content, react-hooks/rules-of-hooks */
            return (
                <>
                    <RetrieveReportsList lens={lens} users={values} />
                    <div className="flex justify-end p-t-10">
                        {renderWizardButtons({
                            onNextClick: () => {
                                save();
                            },
                            nextButtonCaption: finishButtonCaption,
                            disableNextButton: formInvalid && isLoading
                        })}
                    </div>
                </>
            );
        },
        [users]
    );

    const isFormInvalid = useCallback((lens) => {
        const usersIds = lens.prop('users').get();
        const from = lens.prop('from').get();
        const to = lens.prop('to').get();

        const fromTimestamp = new Date(from).getTime();
        const toTimestamp = new Date(to).getTime();

        const datesInvalid = !fromTimestamp || !toTimestamp || fromTimestamp > toTimestamp;

        return !usersIds || !usersIds.length || datesInvalid;
    }, []);

    const handleSave = useCallback(async (values: Report) => {
        const { users, from, to } = values;
        const userIds = users!.map((user) => user.id);
        const formattedFrom = `${from} ${timeAppendix}`;
        const formattedTo = `${to} ${timeAppendix}`;

        const fileName = `Reports ${from}-${to}.csv`;

        download(
            useDownloadTaskReport({ userIds, from: formattedFrom, to: formattedTo }),
            fileName
        );
    }, []);

    const getMetaData = useCallback(
        (): Metadata<Report> => ({
            props: {
                users: {
                    isRequired: true
                },
                from: {
                    isRequired: true
                },
                to: {
                    isRequired: true
                }
            }
        }),
        []
    );

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <div
                className={`${styles['title']} flex justify-between align-vert-center ${styles.title}`}
            >
                <MultiSwitchMenu items={ML_MENU_ITEMS} currentPath={history.location.pathname} />
            </div>
            <a href={url} download={name} className="hidden" ref={ref} />
            <div className={styles['form-group']}>
                <Form<Report>
                    renderForm={renderForm}
                    onSave={handleSave}
                    getMetadata={getMetaData}
                    value={{ ...initialValues, users: [] }}
                />
            </div>
        </Panel>
    );
};
