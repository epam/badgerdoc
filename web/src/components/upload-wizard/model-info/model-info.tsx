import React, { FC } from 'react';
import { useModelById } from '../../../api/hooks/models';
import styles from '../preprocessor/upload-wizard-preprocessor.module.scss';
import { Tooltip } from '@epam/loveship';

type ModelInfoProps = {
    id: string;
    ver?: number;
};

const ModelInfo: FC<ModelInfoProps> = ({ id, ver }) => {
    const { data: model } = useModelById(
        {
            modelId: id,
            modelVer: ver
        },
        {
            refetchInterval: false
        }
    );

    return (
        <Tooltip content={model?.description}>
            <div className={styles.model}>
                {model?.name} v{model?.version}
            </div>
        </Tooltip>
    );
};

export default ModelInfo;
