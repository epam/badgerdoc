import React, { useCallback, useState, useContext } from 'react';
import {
    Button,
    FlexRow,
    FlexCell,
    FlexSpacer,
    SearchInput,
    PickerInput,
    Text,
    MultiSwitch,
    UploadFileToggler
} from '@epam/loveship';
import { useHistory } from 'react-router-dom';
import { useArrayDataSource } from '@epam/uui';
import { getError } from 'shared/helpers/get-error';
import styles from './documents-page-control-connector.module.scss';
import { DocumentsFilterCardIcon } from './documents-filter-card-icon';
import { DocumentsFilterListIcon } from './documents-filter-list-icon';
import { BreadcrumbNavigation } from 'shared/components/breadcrumb';
import { DocumentsSearch } from 'shared/contexts/documents-search';
import { ReactComponent as WizardIcon } from 'icons/wizard.svg';
import { useNotifications } from '../../shared/components/notifications';
import { useUploadFilesMutation } from '../../api/hooks/documents';

type DocumentsPageControlProps = {
    isSearchPage?: boolean;
    handleUploadWizardButtonClick: () => void;
    onSearchClick: () => void;
};

const sortPiecesItems = [
    { id: 'relevancy', name: 'Relevancy' },
    { id: 'category', name: 'Category' }
];

const sortFilesItems = [
    { id: 'last_modified', name: 'Last Modified' },
    { id: 'original_name', name: 'Name' }
];

export const DocumentsPageControlConnector = ({
    isSearchPage,
    handleUploadWizardButtonClick
}: DocumentsPageControlProps) => {
    const history = useHistory();
    const uploadFilesMutation = useUploadFilesMutation();
    const dataSortSource = useArrayDataSource(
        {
            items: isSearchPage ? sortPiecesItems : sortFilesItems
        },
        [isSearchPage]
    );

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const { notifyError, notifySuccess } = useNotifications();

    const {
        query,
        documentView,
        breadcrumbs,
        documentsSort,
        setQuery,
        setDocumentView,
        setDocumentsSort
    } = useContext(DocumentsSearch);

    const isCard = documentView === 'card';
    const isTable = documentView === 'table';

    const handleAddFiles = useCallback(async (files: File[]) => {
        if (!files?.length) return;

        try {
            setIsLoading(true);
            const responses = await uploadFilesMutation.mutateAsync([...files]);

            for (const response of responses) {
                notifySuccess(<Text>{response.message}</Text>);
            }
        } catch (error) {
            notifyError(<Text>{getError(error)}</Text>);
        } finally {
            setIsLoading(false);
        }
    }, []);

    return (
        <>
            <FlexRow alignItems="center" cx={styles['header-container']}>
                <BreadcrumbNavigation breadcrumbs={breadcrumbs} />
                <FlexSpacer />
                <FlexRow>
                    <FlexRow padding="6">
                        <UploadFileToggler
                            onFilesAdded={handleAddFiles}
                            render={({ onClick }) => (
                                <Button caption="Upload" isDisabled={isLoading} onClick={onClick} />
                            )}
                        />
                    </FlexRow>
                    <FlexRow padding="6">
                        <Button
                            caption="Upload Wizard"
                            onClick={handleUploadWizardButtonClick}
                            color="grass"
                            icon={WizardIcon}
                        />
                    </FlexRow>
                </FlexRow>
            </FlexRow>
            <FlexRow spacing="12">
                <FlexCell grow={1}>
                    <SearchInput
                        value={query}
                        onValueChange={(value) => setQuery(value || '')}
                        placeholder={`Search in ${isSearchPage ? 'documents' : 'files'}`}
                        debounceDelay={500}
                    />
                </FlexCell>
                <MultiSwitch
                    onValueChange={(newValue) => {
                        switch (newValue) {
                            case 'document':
                                history.push('/documents/search');
                                break;
                            case 'file':
                                history.push('/documents');
                                break;
                            default:
                                history.push('/documents');
                        }
                    }}
                    items={[
                        { id: 'document', caption: 'in documents' },
                        { id: 'file', caption: 'in file names' }
                    ]}
                    value={isSearchPage ? 'document' : 'file'}
                    color="night600"
                />
                {isCard && (
                    <FlexRow cx={styles['search-filter']}>
                        <span className={styles['sort-name']}>Sort by:</span>
                        <PickerInput
                            minBodyWidth={100}
                            dataSource={dataSortSource}
                            value={documentsSort}
                            onValueChange={setDocumentsSort}
                            getName={(item: any) => item.name}
                            disableClear
                            selectionMode="single"
                            valueType={'id'}
                        />
                    </FlexRow>
                )}
                <FlexRow>
                    <DocumentsFilterCardIcon
                        isDisable={!!isSearchPage}
                        onDocViewChange={setDocumentView}
                        isActive={isCard}
                    />
                    <DocumentsFilterListIcon
                        isDisable={!!isSearchPage}
                        onDocViewChange={setDocumentView}
                        isActive={isTable}
                    />
                </FlexRow>
            </FlexRow>
        </>
    );
};
