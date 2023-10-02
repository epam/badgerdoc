// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import React from 'react';
import { useAssetById } from '../../../api/hooks/assets';
import { useTaskAnnotatorContext } from '../../../connectors/task-annotator-connector/task-annotator-context';
import { PDFPageProxy } from 'react-pdf';

type ImageProps = {
    id: number;
    handlePageLoaded: (page: PDFPageProxy | HTMLImageElement) => void;
};

export const Image: React.FC<ImageProps> = ({ id, handlePageLoaded }) => {
    const { fileMetaInfo } = useTaskAnnotatorContext();
    const imageFile = useAssetById(
        { fileId: id },
        {
            refetchInterval: 100000
        }
    );

    if (imageFile?.data)
        return (
            <img
                src={URL.createObjectURL(imageFile?.data || {})}
                alt={''}
                id="image-annotation"
                onLoad={(e) => {
                    handlePageLoaded(e.target as HTMLImageElement);
                    fileMetaInfo.imageSize = {
                        width: (e.target as HTMLDivElement).offsetWidth,
                        height: (e.target as HTMLDivElement).offsetHeight
                    };
                }}
                style={{ width: '100%' }}
            />
        );
    return null;
};
