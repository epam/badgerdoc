// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useCallback, useContext } from 'react';
import { IconButton, Dropdown, Checkbox } from '@epam/loveship';
import { ReactComponent as jobsPicture } from '@epam/assets/icons/common/navigation-chevron-down-24.svg';
import { ReactComponent as FileDownloadFillIcon } from '@epam/assets/icons/common/file-download-24.svg';
import { ErrorNotification, IDropdownToggler, INotification } from '@epam/uui';
import { Status } from 'shared/components/status';
import { mapStatusForJobs } from 'shared/helpers/map-statuses';
import { Job, JobStatus } from 'api/typings/jobs';
import { Link } from 'react-router-dom';
import { fetchLatestAnnotations, useThumbnailPiece } from 'api/hooks/assets';
import { SelectedFilesContext } from 'shared/contexts/SelectedFilesContext';
import styles from './document-card-view-item.module.scss';
import { getError } from 'shared/helpers/get-error';
import { svc } from 'services';

type DocumentCardViewProps = {
    isPieces?: boolean;
    lastModified?: string;
    documentPage?: number;
    jobs: Job[];
    documentId: number;
    documentName: string | number;
    thumbnails?: Record<number, string>;
    bbox?: number[];
};

const isDocumentId = (selectedFiles: number[], documentId: number): boolean => {
    return selectedFiles.includes(documentId);
};

export const DocumentCardViewItem: FC<DocumentCardViewProps> = ({
    isPieces,
    lastModified,
    jobs,
    documentPage,
    documentId,
    documentName,
    thumbnails,
    bbox
}) => {
    const { selectedFiles, setSelectedFiles } = useContext(SelectedFilesContext);
    const thumbnailPiece = useThumbnailPiece(
        { fileId: documentId, pageNum: documentPage, bbox },
        {}
    );

    const renderJobsDropdown = (jobs: Job[]) => {
        return (
            <div className={styles['list']}>
                {jobs.map((job) => (
                    <Link to={getDocumentPath(job.id)} key={job.id} className={styles['list-item']}>
                        {job.status && (
                            <Status
                                isTooltip
                                placementTooltip={'left'}
                                statusTitle={job.status}
                                color={mapStatusForJobs(job.status, 'Automatic').color}
                            />
                        )}
                        <div className={styles['jobs-list-item-text']}>{job.name}</div>
                    </Link>
                ))}
            </div>
        );
    };

    const getDocumentPath = (nextJobId: number | null): string => {
        let path = `/documents/${documentId}`;
        if (jobs && jobs.length) {
            return path + `?jobId=${nextJobId ?? jobs[0].id}`;
        }
        return path;
    };

    const handleError = useCallback((err: unknown) => {
        svc.uuiNotifications.show(
            (props: INotification) => (
                <ErrorNotification {...props}>
                    <div>{getError(err)}</div>
                </ErrorNotification>
            ),
            { duration: 2 }
        );
    }, []);

    const downloadFile = (blob: Blob, fileName: string) => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(link.href);
    };

    const handleDownloadDocument = async (event: React.MouseEvent) => {
        event.preventDefault();
        try {
            const blob = await fetchLatestAnnotations(documentId);
            downloadFile(blob, String(documentName));
        } catch (error) {
            handleError(error);
        }
    };

    const handleCheckboxChange = (newValue: boolean) => {
        const newSelectedFiles = newValue
            ? [...selectedFiles, documentId]
            : selectedFiles.filter((id) => id !== documentId);
        setSelectedFiles(newSelectedFiles);
    };

    const handleCheckboxClick = (event: React.MouseEvent) => {
        event.stopPropagation(); // Prevent click from triggering Link navigation
    };

    return (
        <Link to={getDocumentPath(null)} className={styles['card-item']}>
            <div className={styles['card-item-padding']}>
                <div className="flex justify-between">
                    <div className={styles['card-item-main']}>
                        <div className={styles['header-container']}>
                            <div className={styles['card-item-title']}>{documentName}</div>
                            <div className={styles['card-item-box']}>
                                <div
                                    role="button"
                                    onClick={handleDownloadDocument}
                                    onKeyPress={(e) => e.key === 'Enter' && handleDownloadDocument}
                                    tabIndex={0}
                                >
                                    <FileDownloadFillIcon
                                        className={styles['card-item-download']}
                                    />
                                </div>
                                {/* temporary_disabled_rules */}
                                {/* eslint-disable jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events */}
                                {!isPieces && (
                                    <div onClick={handleCheckboxClick}>
                                        <Checkbox
                                            value={isDocumentId(selectedFiles, documentId)}
                                            onValueChange={handleCheckboxChange}
                                            aria-label={`Select document ${documentName}`}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                        {jobs && jobs.length ? (
                            <div className={styles['jobs-container']}>
                                {jobs.length > 1 ? (
                                    <Dropdown
                                        openOnHover
                                        closeOnMouseLeave="boundary"
                                        renderBody={() => renderJobsDropdown(jobs)}
                                        renderTarget={(props: IDropdownToggler) => (
                                            <div {...props} className="flex">
                                                <span className={styles['jobs-text']}>
                                                    {jobs.length} jobs
                                                </span>
                                                <IconButton icon={jobsPicture} />
                                            </div>
                                        )}
                                    />
                                ) : (
                                    <div className="flex flex-center">
                                        <Status
                                            isTooltip
                                            placementTooltip={'left'}
                                            statusTitle={jobs[0].status!}
                                            color={
                                                mapStatusForJobs(jobs[0].status!, 'Automatic').color
                                            }
                                        />
                                        <span className={`${styles['jobs-text']} m-l-5`}>
                                            {jobs[0].name}
                                        </span>
                                    </div>
                                )}
                                <span className={styles['jobs-text']}>
                                    {isPieces
                                        ? `p. ${documentPage}`
                                        : lastModified &&
                                          new Date(lastModified).toLocaleDateString()}
                                </span>
                            </div>
                        ) : (
                            <div />
                        )}
                    </div>
                </div>
            </div>
            {!isPieces && (
                <div
                    className={styles['image-container']}
                    style={{
                        background: `url(${(thumbnails as any)[documentId]})`
                    }}
                />
            )}
            {isPieces && thumbnailPiece.data && (
                <div
                    className={styles['image-container']}
                    style={{
                        background: `url(${thumbnailPiece.data})`
                    }}
                />
            )}
        </Link>
    );
};
