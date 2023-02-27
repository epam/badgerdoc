import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useJobById } from '../../api/hooks/jobs';
import { useUserByForJob } from '../../api/hooks/users';
import {
    FlexRow,
    FlexSpacer,
    IconButton,
    LinkButton,
    Panel,
    SearchInput,
    VirtualList
} from '@epam/loveship';
import { FilterWithDocumentExtraOption, Operators, User } from '../../api/typings';
import { VirtualListState } from '@epam/uui';
import { JobSidebarHeader } from '../../shared/components/job/job-sidebar-header';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-back-18.svg';

import styles from './jod-detailed-sidebar-connector.module.scss';
import { SidebarRowSelection } from 'shared/components/sidebar/sidebar-row-selection/sidebar-row-selection';

type JobDetailViewSideBarProps = {
    jobId: number;
    onUserClick: (user?: User) => void;
    activeUser?: User;
    activeTab: string;
};

export const JobSidebarConnector: React.FC<JobDetailViewSideBarProps> = ({
    jobId,
    onUserClick,
    activeUser,
    activeTab
}) => {
    const { data: job } = useJobById({ jobId }, {});
    const [annotators, setAnnotators] = useState<User[]>([]);
    const [listState, setListState] = useState<VirtualListState>({});
    const [usersRows, setUsersRows] = useState<any>();
    const [searchText, setSearchText] = useState('');
    const filtersRef = useRef<FilterWithDocumentExtraOption<keyof User>[]>([]);

    const onSearchChange = (text: string) => {
        setSearchText(text);
    };

    const { data: users } = useUserByForJob(
        {
            page: 1,
            size: 100,
            filters: filtersRef.current
        },
        {}
    );
    useEffect(() => {
        if (searchText) {
            filtersRef.current = [
                {
                    field: 'username',
                    operator: Operators.LIKE,
                    value: `${searchText}`
                }
            ];
        }
    }, [searchText]);

    useEffect(() => {
        if (users && job && Array.isArray(users.data) && job.annotators) {
            const filteredUsers = users?.data.filter((user) => {
                return job.annotators.includes(user.id);
            });
            setAnnotators(filteredUsers);
        }
    }, [job?.annotators, users?.data]);

    useEffect(() => {
        if (annotators && Array.isArray(annotators)) {
            let users = [...annotators];
            if (searchText) {
                users = users.filter((annotator) => {
                    return annotator.username.includes(searchText);
                });
            }
            const elements = users.map((user) => {
                return (
                    <SidebarRowSelection
                        key={user.id}
                        entity={user}
                        activeEntity={activeUser}
                        onEntitySelect={onUserClick}
                    >
                        <FlexRow key={user.id} cx="flex align-center">
                            <LinkButton
                                isDisabled={activeTab !== 'Tasks'}
                                caption={`${user.username}`}
                                size="42"
                                cx={styles.text}
                                color="night900"
                            />
                            <FlexSpacer />
                        </FlexRow>
                    </SidebarRowSelection>
                );
            });

            setUsersRows(elements);
        }
    }, [annotators, searchText, activeTab, activeUser]);
    const [isOpened, setIsOpened] = useState(true);

    const toggle = () => setIsOpened((v) => !v);

    const sidebarPanelClassname = useMemo(
        () =>
            `${styles['sidebar-panel-wrapper']} ${
                isOpened ? styles['sidebar-panel-opened'] : styles['sidebar-panel-closed']
            }`,
        [isOpened, styles]
    );

    const iconClassname = useMemo(
        () => `${styles['icon']} ${isOpened ? styles['close-icon'] : styles['open-icon']}`,
        [isOpened, styles]
    );

    return (
        <>
            <div className={sidebarPanelClassname}>
                <Panel cx={styles.panel}>
                    <JobSidebarHeader job={job} />
                    {job?.type !== 'ExtractionJob' && (
                        <>
                            <div className={styles.annotators}>
                                <h3>Annotators:</h3>
                                <SearchInput
                                    value={searchText}
                                    onValueChange={(newValue) => onSearchChange(newValue ?? '')}
                                    placeholder="Search annotators"
                                    debounceDelay={500}
                                />
                                {activeTab === 'Tasks' && (
                                    <LinkButton
                                        fontSize="16"
                                        caption={'All Annotators'}
                                        onClick={() => onUserClick(undefined)}
                                    />
                                )}
                            </div>
                            <VirtualList
                                rows={usersRows}
                                value={listState}
                                onValueChange={setListState}
                            />
                        </>
                    )}
                </Panel>
                <IconButton cx={iconClassname} icon={closeIcon} onClick={toggle} color="sky" />
            </div>
        </>
    );
};
