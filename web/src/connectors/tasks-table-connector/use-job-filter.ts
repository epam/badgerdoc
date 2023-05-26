import { useLazyDataSource } from '@epam/uui';
import { jobPropFetcher } from 'api/hooks/jobs';
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
        cache: Array<string>;
        search: string;
    };

    const loadJobs = createPagingCachedLoader(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await jobPropFetcher('name', pageNumber, pageSize, keyword)
    );

    const jobNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadJobs,
            getId: (job) => job.toString()
        },
        []
    );

    const renderJobFilter = useColumnPickerFilter<string, string, unknown, string>(
        jobNames,
        fieldName,
        {
            showSearch: true
        }
    );
    return renderJobFilter;
};
