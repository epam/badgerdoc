const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

export const getPdfDocumentAddress = (documentId: number) => {
    return `${namespace}/download?file_id=${documentId}`;
};
