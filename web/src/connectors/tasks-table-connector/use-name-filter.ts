import { useLazyDataSource } from '@epam/uui';
import { documentsFetcher } from 'api/hooks/documents';
import { FileDocument } from 'api/typings';
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
        cache: FileDocument[];
        search: string;
    };

    const loadDocuments = createPagingCachedLoader(
        namesCache,
        async (pageNumber, pageSize, keyword) =>
            await documentsFetcher(pageNumber, pageSize, keyword)
    );

    const documentNames = useLazyDataSource<FileDocument, string, unknown>(
        {
            api: loadDocuments,
            getId: (doc) => doc.id.toString()
        },
        []
    );

    const renderNameFilter = useColumnPickerFilter<FileDocument, string, unknown, string>(
        documentNames,
        fieldName,
        {
            showSearch: true,
            getName: (item) => (typeof item === 'boolean' ? String(item) : item.original_name)
        }
    );
    return renderNameFilter;
};
