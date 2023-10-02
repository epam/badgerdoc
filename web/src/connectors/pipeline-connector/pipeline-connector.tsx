// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { usePipelineByName } from 'api/hooks/pipelines';
import PipelineComponent from 'components/pipeline/pipeline-component/pipeline-component';
import { PipelineTextArea } from 'components/pipeline/pipeline-text-area/pipeline-text-area';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type PipelineConnectorProps = {
    pipelineName?: string;
};

export const PipelineConnector: FC<PipelineConnectorProps> = ({ pipelineName }) => {
    const [currentVersion, setCurrentVersion] = useState<number | undefined>(undefined);
    const [bufVersion, setBufVersion] = useState<number | undefined>(undefined);
    const { data: pipeline, refetch: refetchPipeline } = usePipelineByName(
        { pipelineName, version: parseInt(`${currentVersion}`) },
        {
            enabled: false,
            cacheTime: 0
        }
    );

    const latestVersion = useMemo(() => {
        if (pipeline?.is_latest) return parseInt(`${pipeline?.version}`);
        return bufVersion;
    }, [pipeline?.name]);

    useEffect(() => {
        setCurrentVersion(pipeline?.version);
    }, [pipelineName]);

    useEffect(() => {
        if (latestVersion) {
            setCurrentVersion(latestVersion);
            setBufVersion(latestVersion);
        }
    }, [latestVersion]);

    useEffect(() => {
        refetchPipeline();
    }, [pipelineName, currentVersion]);

    if (!pipelineName) {
        return <div>Please select pipeline</div>;
    }

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <PipelineComponent
                key={pipeline?.id}
                readOnly
                pipeline={pipeline}
                currentVersion={pipeline?.version}
                latestVersion={latestVersion}
                changeVersion={setCurrentVersion}
            />
            <div className={wizardStyles['content__editor']}>
                <PipelineTextArea
                    text={pipeline?.summary ?? ''}
                    title={'Short description for a whole pipeline'}
                />
                <PipelineTextArea
                    text={pipeline?.description ?? ''}
                    title={'Full description for a specific version'}
                />
            </div>
        </div>
    );
};

export default React.memo(PipelineConnector);
