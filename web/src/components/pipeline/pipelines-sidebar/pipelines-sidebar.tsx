// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useEffect, useState } from 'react';
import { DocumentsSidebarConnector, RenderCreateBtn } from 'connectors/documents-sidebar-connector';
import { usePipelines } from 'api/hooks/pipelines';
import { Operators, Pipeline, SortingDirection } from 'api/typings';
import SidebarButton from 'shared/components/sidebar/sidebar-button/sidebar-button';
import { FlexRow, LinkButton } from '@epam/loveship';
import styles from './pipelines-sidebar.module.scss';
import { SidebarRowSelection } from 'shared/components/sidebar/sidebar-row-selection/sidebar-row-selection';

type PipelinesSidebarProps = {
    onAddPipeline: () => void;
    onSelectPipeline: (pipeline?: Pipeline) => void;
};

export const PipelinesSidebar: FC<PipelinesSidebarProps> = ({
    onAddPipeline,
    onSelectPipeline
}) => {
    const { data: pipelines } = usePipelines(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC },
            filters: [
                {
                    field: 'is_latest',
                    operator: Operators.EQ,
                    value: true
                }
            ]
        },
        {}
    );
    const [activePipeline, setActivePipeline] = useState<Pipeline | undefined>(pipelines?.data[0]);

    useEffect(() => {
        setActivePipeline(pipelines?.data[0]);
    }, [pipelines?.data]);

    useEffect(() => {
        onSelectPipeline(activePipeline);
    }, [activePipeline]);

    const renderCreateBtn: RenderCreateBtn = () => (
        <SidebarButton onClick={onAddPipeline} caption="Add new pipeline" />
    );

    return (
        <DocumentsSidebarConnector
            title="Pipelines"
            useEntitiesHook={usePipelines}
            filters={[
                {
                    field: 'is_latest',
                    operator: Operators.EQ,
                    value: true
                }
            ]}
            activeEntity={activePipeline}
            sortField="name"
            renderCreateBtn={renderCreateBtn}
            rowRender={(pipeline) => (
                // todo: these types mismatches should probably be fixed in other way
                <SidebarRowSelection
                    entity={pipeline}
                    activeEntity={activePipeline}
                    onEntitySelect={setActivePipeline as (entity: { id: string | number }) => void}
                >
                    <FlexRow padding="18" key={pipeline.name}>
                        <LinkButton
                            caption={`${pipeline.name}`}
                            size="42"
                            color="night900"
                            cx={styles.text}
                        />
                    </FlexRow>
                </SidebarRowSelection>
            )}
        />
    );
};

export default PipelinesSidebar;
