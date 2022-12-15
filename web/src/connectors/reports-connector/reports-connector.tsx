import React, { FC, useCallback, useEffect, useState } from 'react';
import { Panel } from '@epam/loveship';
import { Form, Metadata, RenderFormProps } from '@epam/uui';
import { useUsers } from 'api/hooks/users';
import { Report, SortingDirection } from 'api/typings';
import { useHistory } from 'react-router-dom';
import { MultiSwitchMenu } from 'shared/components/multi-switch-menu/MultiSwitchMenu';
import { ML_MENU_ITEMS } from 'shared/contexts/current-user';
import styles from './reports-connector.module.scss';
import RetrieveReportsList from 'components/reports/retrieve-reports-list';
import { renderWizardButtons } from 'shared/components/wizard/wizard/wizard';
import { useDownloadTaskReport } from 'api/hooks/tasks';
import { useDownloadFile } from 'shared/hooks/use-download-file';

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

    const { ref, url, download, name } = useDownloadFile({
        preDownloading: () => setLoading(true),
        postDownloading: () => setLoading(false),
        onError: () => setLoading(false)
    });

    const renderForm = useCallback(({ lens, save }: RenderFormProps<Report>) => {
        const values = users.data?.data;

        const formInvalid = isFormInvalid(lens);
        /* eslint-disable jsx-a11y/anchor-has-content */
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
    }, []);

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

        try {
            download(
                useDownloadTaskReport({ userIds, from: formattedFrom, to: formattedTo }),
                fileName
            );
        } catch (err: any) {
            console.error('The error has occured: ', err.message);
        }
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
            <div>
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
