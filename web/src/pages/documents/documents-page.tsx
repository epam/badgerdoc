// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { useCallback, useState } from 'react';
import { Sidebar } from 'shared';
import {
    DocumentsSidebarConnector,
    DocumentsTableConnector,
    RenderCreateBtn,
    DocumentsPageControlConnector,
    DocumentsSearchConnector,
    DocumentsCardConnector
} from 'connectors';
import { Switch, Route, useRouteMatch, useHistory, Redirect } from 'react-router-dom';
import { useDatasets } from 'api/hooks/datasets';
import { Dataset } from 'api/typings';
import AddDatasetConnector from 'connectors/add-dataset-connector/add-dataset-connector';
import { DocumentPageConnector } from '../../connectors/document-page-connector/document-page-connector';
import { DatasetRow } from 'components/dataset/dataset-row/dataset-row';
import { DocumentsSearchProvider } from 'shared/contexts/documents-search';
import { UploadWizardPage } from '../upload-document-wizard/upload-document-wizard-page';
import { JOBS_PAGE } from '../../shared/constants/general';
import { DocumentsDropZone } from 'components/documents/documents-drop-zone/documents-drop-zone';
import { UploadIndicatorContextProvider } from 'components/upload-indicator/upload-indicator.context';

const DocumentsPage = () => {
    const history = useHistory();
    const { path } = useRouteMatch();

    const [activeDataset, setActiveDataset] = useState<Dataset | null | undefined>(null);
    const [fileIds, setFileIds] = useState<Array<number>>([]);

    const [isFileOver, setFileOver] = useState<boolean>(false);

    const onFileSelect = useCallback((ids) => {
        setFileIds(ids);
    }, []);

    const handleUploadWizardButtonClick = useCallback(() => {
        history.push(`${path}/upload-wizard`);
    }, []);

    const onSearchClick = useCallback(() => {
        history.push(`${path}/search`);
    }, []);

    const handleDatasetSelected = (dataset?: Dataset | null) => {
        setActiveDataset(dataset);
        return history.push(`${path}`);
    };

    const handleJobAddClick = () => {
        return history.push({
            pathname: `${JOBS_PAGE}/add`,
            state: {
                files: fileIds
            }
        });
    };

    const handleRowClick = (id: number) =>
        history.push({
            pathname: `${path}/${id}`
        });

    const rowRender = (dataset: Dataset) => {
        return (
            <DatasetRow
                dataset={dataset}
                onDatasetClick={handleDatasetSelected}
                activeDataset={activeDataset}
            />
        );
    };

    const renderCreateBtn: RenderCreateBtn = ({ onCreated }) => (
        <AddDatasetConnector onCreated={onCreated} />
    );

    return (
        <DocumentsSearchProvider>
            <Switch>
                <Route exact path={path}>
                    <Sidebar
                        sideContent={
                            <DocumentsSidebarConnector
                                title="Datasets"
                                resetCaption="All documents"
                                useEntitiesHook={useDatasets}
                                activeEntity={activeDataset}
                                onReset={() => handleDatasetSelected(null)}
                                rowRender={rowRender}
                                renderCreateBtn={renderCreateBtn}
                                sortField="name"
                            />
                        }
                        mainContent={
                            <div
                                onDragOver={() => setFileOver(true)}
                                onDragLeave={() => setFileOver(false)}
                                onDrop={() => setFileOver(false)}
                                style={{
                                    height: '100%',
                                    overflow: 'hidden',
                                    display: 'flex',
                                    flexDirection: 'column'
                                }}
                            >
                                <DocumentsDropZone dataset={activeDataset}>
                                    {!isFileOver && (
                                        <DocumentsTableConnector
                                            dataset={activeDataset}
                                            onRowClick={handleRowClick}
                                            fileIds={fileIds}
                                            onFilesSelect={onFileSelect}
                                            handleJobAddClick={handleJobAddClick}
                                            withHeader
                                        />
                                    )}
                                </DocumentsDropZone>
                            </div>
                        }
                        sidebarHeaderContent={
                            <UploadIndicatorContextProvider>
                                <DocumentsPageControlConnector
                                    handleUploadWizardButtonClick={handleUploadWizardButtonClick}
                                    onSearchClick={onSearchClick}
                                />
                            </UploadIndicatorContextProvider>
                        }
                    />
                </Route>
                <Route path={`${path}/upload-wizard`} component={UploadWizardPage} />
                <Route path={`${path}/search`}>
                    <Sidebar
                        sideContent={<DocumentsSearchConnector />}
                        mainContent={
                            <div
                                onDragOver={() => setFileOver(true)}
                                onDragLeave={() => setFileOver(false)}
                                onDrop={() => setFileOver(false)}
                                style={{
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    overflow: 'hidden'
                                }}
                            >
                                <DocumentsDropZone dataset={activeDataset}>
                                    {!isFileOver && (
                                        <DocumentsCardConnector onFilesSelect={onFileSelect} />
                                    )}
                                </DocumentsDropZone>
                            </div>
                        }
                        sidebarHeaderContent={
                            <UploadIndicatorContextProvider>
                                <DocumentsPageControlConnector
                                    isSearchPage
                                    handleUploadWizardButtonClick={handleUploadWizardButtonClick}
                                    onSearchClick={onSearchClick}
                                />
                            </UploadIndicatorContextProvider>
                        }
                    />
                </Route>
                <Route path={`${path}/:documentId`} component={DocumentPageConnector} />
                <Redirect to={path} />
            </Switch>
        </DocumentsSearchProvider>
    );
};

export default React.memo(DocumentsPage);
