import { useBadgerFetch } from 'api/hooks/api';
import { Ketcher } from 'ketcher-core';
import { Editor } from 'ketcher-react';
import { StandaloneStructServiceProvider } from 'ketcher-standalone';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { useEffect } from 'react';
import { useQuery } from 'react-query';
import { getPdfDocumentAddress } from 'shared/helpers/get-pdf-document-address';

const structServiceProvider = new StandaloneStructServiceProvider();

interface DocumentMolProps {
    fileMetaInfo: FileMetaInfo;
    editable: boolean;
}

async function FetchMolecule(fileId: number): Promise<any> {
    return useBadgerFetch({
        url: getPdfDocumentAddress(fileId),
        method: 'get',
        withCredentials: true,
        isText: true
    })();
}

const DocumentMol = ({ fileMetaInfo, editable }: DocumentMolProps) => {
    const fileId = fileMetaInfo.id;
    const {
        data: molecule,
        isLoading,
        error
    } = useQuery(['molecule', fileId], () => FetchMolecule(fileMetaInfo.id));
    useEffect(() => {}, []);
    if (isLoading || error) {
        return null;
    }
    return (
        <Editor
            staticResourcesUrl=""
            structServiceProvider={structServiceProvider}
            onInit={(ketcherObj: Ketcher) => {
                if (molecule) {
                    ketcherObj.setMolecule(molecule);
                }
            }}
            errorHandler={() => {}}
        />
    );
};

export default DocumentMol;
