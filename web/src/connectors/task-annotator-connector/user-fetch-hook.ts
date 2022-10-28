import { Job } from '../../api/typings/jobs';
import { Filter, Operators, PagedResponse, User } from '../../api/typings';
import { useJobById } from '../../api/hooks/jobs';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useUserByForJob } from '../../api/hooks/users';
import { Task } from '../../api/typings/tasks';
import uniq from 'lodash/uniq';

type SortedUsersType = { owners: User[]; annotators: User[]; validators: User[] };

export const useUsersDataFromTask = (task: Task | undefined) => {
    const [isOwner, setIsOwner] = useState(false);
    const sortedUsers = useRef<SortedUsersType>({
        owners: [],
        annotators: [],
        validators: []
    });
    const usersFilters = useRef<Filter<keyof User>[]>([]);

    const { data: job, refetch: refetchJob } = useJobById(
        { jobId: task?.job?.id || 0 },
        { enabled: false }
    );
    const { data: users } = useUserByForJob(
        { page: 1, size: 15, filters: usersFilters.current },
        {}
    );

    useEffect(() => {
        if (!task) return;
        refetchJob();
    }, [task]);

    useEffect(() => {
        if (job) {
            const { owners, annotators, validators } = job;
            const usersArr = uniq([...validators, ...annotators, ...owners]);
            usersFilters.current = [
                {
                    field: 'id',
                    operator: Operators.IN,
                    value: usersArr
                }
            ];
            if (task && job.owners.includes(task.user_id)) setIsOwner(true);
        }
    }, [job, task]);

    useEffect(() => {
        if (users?.data && job) {
            sortedUsers.current = mapUsersFromServer(job, users);
        }
    }, [users?.data, job]);

    return useMemo(
        () => ({
            isOwner,
            sortedUsers
        }),
        [task]
    );
};

const mapUsersFromServer = (job: Job, usersArray: PagedResponse<User>) => {
    if (usersArray.data.length === 0) return {} as SortedUsersType;
    const sortedUserObject: SortedUsersType = ['owners', 'annotators', 'validators'].reduce(
        (acc, key) => {
            const userKey = key as keyof SortedUsersType;
            acc[userKey] = usersArray.data.filter((user) => job[userKey].includes(user.id));
            return acc;
        },
        {} as SortedUsersType
    );
    return sortedUserObject;
};
