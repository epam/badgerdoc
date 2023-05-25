import { useLazyDataSource } from '@epam/uui';
import { documentNamesFetcher } from 'api/hooks/document';
import { useRef } from 'react';
import { useColumnPickerFilter } from 'shared/components/filters/column-picker';
import { createPagingCachedLoader } from 'shared/helpers/create-paging-cached-loader';

type Props = {
    fieldName: string;
};

export const useNameFilter = ({ fieldName }: Props) => {
    const namesCache = useRef<PagingCache>({
        page: -1,
        cache: [],
        search: ''
    });

    type PagingCache = {
        page: number;
        cache: string[];
        search: string;
    };

    const loadDocumentsNames = createPagingCachedLoader(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await documentNamesFetcher(pageNumber, pageSize, [], keyword)
    );

    const documentNames = useLazyDataSource<string, string, unknown>(
        {
            api: loadDocumentsNames,
            getId: (doc) => doc.toString()
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<string, string, unknown, string>(
        documentNames,
        fieldName,
        {
            showSearch: true
        }
    );
    return renderNameFilter;
};
