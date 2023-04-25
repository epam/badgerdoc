import React from 'react';
import { MODELS_PAGE } from '../../../shared/constants/general';
import { BreadcrumbNavigation } from '../../../shared/components/breadcrumb';
import { deployModel, undeployAndDeleteModel } from '../../../api/hooks/models';
import { getError } from '../../../shared/helpers/get-error';
import { useHistory } from 'react-router-dom';

import { Button, FlexCell, FlexRow } from '@epam/loveship';
import styles from '../../../shared/components/job/job-header.module.scss';

type ModelHeaderProps = {
    name: string;
    modelId: string;
    version: string;
};

export const ModelHeader: React.FC<ModelHeaderProps> = ({ name, modelId, version }) => {
    const history = useHistory<Record<string, string | undefined>>();

    const handleDeployClick = async (modelId: string) => {
        try {
            await deployModel(modelId);
        } catch (error) {
            console.error(getError(error));
        }
    };

    const handleDeleteClick = async (modelId: string) => {
        try {
            await undeployAndDeleteModel(modelId);
            history.push('/models');
        } catch (error) {
            console.error(getError(error));
        }
    };

    const handleEditClick = (modelId: string, version: string) => {
        history.push(`/models/${modelId}/${version ?? ''}/edit`);
    };

    return (
        <FlexCell>
            <FlexRow alignItems="center">
                <FlexRow cx={styles.container}>
                    <FlexRow alignItems="center">
                        <BreadcrumbNavigation
                            breadcrumbs={[
                                { name: 'Models', url: MODELS_PAGE },
                                { name: `${name || null} model` }
                            ]}
                        />
                    </FlexRow>
                    <FlexRow>
                        <Button caption="Deploy" onClick={() => handleDeployClick(modelId)} />
                        <Button caption="Edit" onClick={() => handleEditClick(modelId, version)} />
                        <Button
                            caption="Delete"
                            onClick={() => handleDeleteClick(modelId)}
                            fill={'white'}
                            color={'fire'}
                        />
                    </FlexRow>
                </FlexRow>
            </FlexRow>
        </FlexCell>
    );
};
