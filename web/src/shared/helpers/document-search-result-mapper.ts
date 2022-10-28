import { parseDate } from './parse-date';
import { FileDocument, PagedResponse } from '../../api/typings';
import { FileMetaInfo } from '../../pages/document/document-page-sidebar-content/document-page-sidebar-content';

export const documentSearchResultMapper = (
    searchResult: PagedResponse<FileDocument> | undefined
): Omit<FileMetaInfo, 'isLoading'> => {
    const item = searchResult?.data ? searchResult.data[0] : null;
    if (item) {
        return {
            id: item.id,
            name: item.original_name,
            pages: item.pages,
            extension: item.extension,
            lastModified: new Date(parseDate(item.last_modified)).toDateString()
        };
    }
    return {
        id: 0,
        name: '',
        pages: 0,
        extension: '',
        lastModified: ''
    };
};
