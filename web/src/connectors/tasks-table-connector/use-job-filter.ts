import { useLazyDataSource } from '@epam/uui';
import { jobsFetcher } from 'api/hooks/jobs';
import { Job } from 'api/typings/jobs';
import { useRef } from 'react';
import { useColumnPickerFilter } from 'shared/components/filters/column-picker';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';

type Props = {
    fieldName: string;
};

export const useJobFilter = ({ fieldName }: Props) => {
    const namesCache = useRef<PagingCache>({
        page: -1,
        cache: [],
        search: ''
    });

    type PagingCache = {
        page: number;
        cache: Array<Job>;
        search: string;
    };

    const loadJobs = createPagingCachedLoader(
        namesCache,
        async (pageNumber, pageSize, keyword) => await jobsFetcher(pageNumber, pageSize, keyword)
    );

    const jobNames = useLazyDataSource<Job, string, unknown>(
        {
            api: loadJobs,
            getId: (job) => job.id.toString()
        },
        []
    );

    const renderJobFilter = useColumnPickerFilter<Job, string, unknown, string>(
        jobNames,
        fieldName,
        {
            showSearch: true,
            getName: (item) => (typeof item === 'boolean' ? String(item) : item.name)
        }
    );
    return renderJobFilter;
};
