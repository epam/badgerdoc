import React, { useMemo, useState } from 'react';
import { useModelById, useModelDeployment, useModelTraining } from '../../api/hooks/models';
import { MultiSwitch } from '@epam/loveship';
import { ModelInfo } from '../../components/model/model-info/model-info';
import { Model, ModelDeployment, Training } from 'api/typings';
import styles from './model-detailed-view-connector.module.scss';
import { ModelHeader } from '../../components/model/model-header/model-header';
import { ModelTraining } from '../../components/model/model-training/model-training';
import { ModelDeploy } from '../../components/model/model-deployment/model-deployment';

type ModelDetailViewProps = {
    modelId: string;
    modelVer: number;
};

export const ModelDetailedViewConnector: React.FC<ModelDetailViewProps> = ({
    modelId,
    modelVer
}) => {
    const [currentView, setCurrentView] = useState('Model');

    const { data: model } = useModelById({ modelId, modelVer }, {});

    const { data: training } = useModelTraining({ trainingId: model?.training_id || 1 }, {});

    const { data: deployment } = useModelDeployment({ modelName: model?.name || '' }, {});

    const view = useMemo(() => {
        if (currentView === 'Model') return <ModelInfo model={model as Model} />;
        else if (currentView === 'Training')
            return <ModelTraining model={model as Model} training={training as Training} />;
        else return <ModelDeploy deployment={deployment as ModelDeployment} />;
    }, [currentView, model, training, deployment]);

    return (
        <div className={styles.container}>
            <ModelHeader name={model?.name || ''} />
            <div className={styles.tabs}>
                <MultiSwitch
                    size="42"
                    items={[
                        {
                            id: 'Model',
                            caption: 'Model'
                        },
                        { id: 'Training', caption: 'Training' },
                        { id: 'Deployment', caption: 'Deployment' }
                    ]}
                    value={currentView}
                    onValueChange={setCurrentView}
                />
            </div>
            <div className={styles.content}>{view}</div>
        </div>
    );
};
