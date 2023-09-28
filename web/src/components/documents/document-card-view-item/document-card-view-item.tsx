// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps*/
import React, { FC, useEffect, useState } from 'react';
import styles from './document-card-view-item.module.scss';
import { IconButton, Dropdown, Checkbox } from '@epam/loveship';
import { ReactComponent as jobsPicture } from '@epam/assets/icons/common/navigation-chevron-down-24.svg';
import { IDropdownToggler } from '@epam/uui';
import { Status } from 'shared/components/status';
import { mapStatusForJobs } from 'shared/helpers/map-statuses';
import { Job, JobStatus } from 'api/typings/jobs';
import { Link } from 'react-router-dom';
import { useThumbnailPiece } from 'api/hooks/assets';

type DocumentCardViewProps = {
    isPieces?: boolean;
    lastModified?: string;
    documentPage?: number;
    jobs: Job[];
    documentId: number;
    name: string | number;
    thumbnails?: {};
    selectedFiles?: number[];
    bbox?: number[];
    setSelectedFiles?: (files: number[]) => void;
};

const isDocumentId = (selectedFiles: number[] | undefined, documentId: number) => {
    if (selectedFiles) {
        return !!selectedFiles.filter((el) => el === documentId).length;
    }
    return false;
};

export const DocumentCardViewItem: FC<DocumentCardViewProps> = ({
    isPieces,
    lastModified,
    jobs,
    documentPage,
    documentId,
    name,
    thumbnails,
    selectedFiles,
    bbox,
    setSelectedFiles
}) => {
    const [chooseFile, setChooseFile] = useState<boolean>(isDocumentId(selectedFiles, documentId));
    const thumbnailPiece = useThumbnailPiece(
        { fileId: documentId, pageNum: documentPage, bbox },
        {}
    );

    useEffect(() => {
        setChooseFile(isDocumentId(selectedFiles, documentId));
    }, [selectedFiles]);

    const renderJobsDropdown = (jobs: any) => {
        return (
            <div className={styles['list']}>
                {jobs.map((job: { name: string; id: number; status: JobStatus }) => (
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

    const getDocumentPath = (nextJobId: null | number) => {
        let path = `/documents/${documentId}`;
        if (jobs && jobs.length) {
            return path + `?jobId=${nextJobId ?? jobs[0].id}`;
        }
        return path;
    };

    return (
        <Link to={getDocumentPath(null)} className={styles['card-item']}>
            <div className={styles['card-item-padding']}>
                <div className="flex justify-between">
                    <div className={styles['card-item-main']}>
                        <div className={styles['header-container']}>
                            <div className={styles['card-item-title']}>{name}</div>
                            {/* temporary_disabled_rules */}
                            {/* eslint-disable jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events */}
                            <div
                                onClick={(event) => {
                                    if (setSelectedFiles) {
                                        event.preventDefault();
                                        if (isDocumentId(selectedFiles, documentId)) {
                                            // @ts-ignore
                                            setSelectedFiles((prevState) => {
                                                const copy = [...prevState].filter(
                                                    (el) => el !== documentId
                                                );
                                                return copy;
                                            });
                                            setChooseFile(false);
                                        } else {
                                            // @ts-ignore
                                            setSelectedFiles((prevState) => {
                                                const copy = [...prevState];
                                                copy.push(documentId);
                                                return copy;
                                            });
                                            setChooseFile(true);
                                        }
                                    }
                                }}
                            >
                                {!isPieces && (
                                    <Checkbox value={chooseFile} onValueChange={() => {}} />
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
