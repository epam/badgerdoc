import React from 'react';
import { Button, FlexCell, FlexRow } from '@epam/loveship';
import styles from '../../../shared/components/job/job-header.module.scss';
import { MODELS_PAGE } from '../../../shared/constants';
import { BreadcrumbNavigation } from '../../../shared/components/breadcrumb';

type ModelHeaderProps = {
    name: string;
    status?: string;
};

// todo: consider removal status param
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const ModelHeader: React.FC<ModelHeaderProps> = ({ name, status }) => {
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
                        <Button caption="Deploy" />
                        <Button caption="Edit" />
                        <Button caption="Delete" fill={'white'} color={'fire'} />
                    </FlexRow>
                </FlexRow>
            </FlexRow>
        </FlexCell>
    );
};
