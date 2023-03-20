import { FilterWithDocumentExtraOption, Operators, TUserShort, User } from '../../api/typings';
import { useJobById } from '../../api/hooks/jobs';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useUserByForJob } from '../../api/hooks/users';
import { Task, TTaskUsers } from '../../api/typings/tasks';
import { Job } from 'api/typings/jobs';

export const useTaskUsers = (task: Task | undefined) => {
    const [isOwner, setIsOwner] = useState(false);
    const usersFilters = useRef<FilterWithDocumentExtraOption<keyof User>[]>([]);
    const taskUsers = useRef<TTaskUsers>({
        owners: [],
        annotators: [],
        validators: []
    });

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
        if (!job) return;

        const { owners, validators } = job;
        const usersArr = new Set([...validators, ...owners]);
        usersFilters.current = [
            {
                field: 'id',
                operator: Operators.IN,
                value: Array.from(usersArr)
            }
        ];

        if (task && job.owners.includes(task.user_id)) {
            setIsOwner(true);
        }
    }, [job, task]);

    useEffect(() => {
        if (!users?.data.length || !job) return;

        taskUsers.current = {
            annotators: job.annotators,
            ...getOwnersAndValidators(users.data, job)
        };
    }, [users?.data, job]);

    return useMemo(
        () => ({
            isOwner,
            taskUsers
        }),
        [task]
    );
};

const getOwnersAndValidators = (users: User[], job: Job) =>
    users.reduce(
        (accumulator: Record<'owners' | 'validators', TUserShort[]>, { id, username }) => {
            if (job.owners.includes(id)) accumulator.owners.push({ id, username });
            if (job.validators.includes(id)) accumulator.validators.push({ id, username });
            return accumulator;
        },
        { owners: [], validators: [] }
    );
