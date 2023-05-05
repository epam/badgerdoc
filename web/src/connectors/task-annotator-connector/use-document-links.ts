import { DocumentLink, DocumentLinkWithName } from 'api/hooks/annotations';
import { useDocuments } from 'api/hooks/documents';
import { FileDocument, Operators } from 'api/typings';
import { Dispatch, SetStateAction, useEffect, useMemo, useState } from 'react';

export interface DocumentLinksValue {
    documentLinks?: DocumentLinkWithName[];
    documentLinksChanged: boolean;
    linksToApi?: DocumentLink[];
    onLinkChanged: (documentId: number, categoryId: string) => void;
    onRelatedDocClick: (documentId?: number) => void;
    selectedRelatedDoc?: FileDocument;
    setDocumentLinksChanged?: Dispatch<SetStateAction<boolean>>;
}

export const useDocumentLinks = (linksFromApi?: DocumentLink[]): DocumentLinksValue => {
    const [selectedRelatedDoc, setSelectedRelatedDoc] = useState<FileDocument | undefined>(
        undefined
    );
    const [documentLinks, setDocumentLinks] = useState<DocumentLinkWithName[]>();
    const [documentLinksChanged, setDocumentLinksChanged] = useState(false);

    const relatedDocsMap = useRelatedDocsMap(linksFromApi);

    useEffect(() => {
        const linksArr: DocumentLinkWithName[] = [];
        if (relatedDocsMap && linksFromApi) {
            for (let link of linksFromApi) {
                linksArr.push({
                    to: link.to,
                    documentName: relatedDocsMap.get(link.to)?.original_name!,
                    category: link.category,
                    type: 'undirectional'
                });
            }
        }
        setDocumentLinks(linksArr);
    }, [relatedDocsMap, linksFromApi]);

    const onLinkChanged = (documentId: number, categoryId: string) => {
        if (relatedDocsMap && documentLinks) {
            const linksArr: DocumentLinkWithName[] = documentLinks.map((documentLink) => {
                if (documentLink.to === documentId) {
                    return {
                        to: documentId,
                        documentName: relatedDocsMap.get(documentId)?.original_name!,
                        category: categoryId,
                        type: 'undirectional'
                    };
                }
                return documentLink;
            });

            setDocumentLinks(linksArr);
            setDocumentLinksChanged(true);
        }
    };

    const onRelatedDocClick = (documentId?: number) => {
        if (relatedDocsMap) {
            setSelectedRelatedDoc(documentId ? relatedDocsMap.get(documentId) : undefined);
        }
    };

    const linksToApi: DocumentLink[] | undefined = useMemo(
        () =>
            documentLinks?.map((documentLink) => ({
                to: documentLink.to,
                category: documentLink.category,
                type: documentLink.type
            })),
        [documentLinks]
    );

    return useMemo(
        () => ({
            documentLinks,
            documentLinksChanged,
            linksToApi,
            onLinkChanged,
            onRelatedDocClick,
            selectedRelatedDoc,
            setDocumentLinksChanged
        }),
        [documentLinks, documentLinksChanged, selectedRelatedDoc]
    );
};

const useRelatedDocsMap = (linksFromApi?: DocumentLink[]): Map<number, FileDocument> | null => {
    const documentIds = useMemo(() => {
        return linksFromApi?.map((link) => link.to);
    }, [linksFromApi]);

    const { data: relatedDocs, refetch: refetchDocs } = useDocuments(
        {
            filters: [
                {
                    field: 'id',
                    operator: Operators.IN,
                    value: documentIds
                }
            ]
        },
        { enabled: false }
    );

    useEffect(() => {
        if (documentIds?.length) {
            refetchDocs();
        }
    }, [documentIds]);

    return useMemo(() => {
        if (!relatedDocs?.data) {
            return null;
        }

        const map = new Map<number, FileDocument>();
        for (const doc of relatedDocs.data) {
            map.set(doc.id, doc);
        }

        return map;
    }, [relatedDocs?.data]);
};
