// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-redeclare */
import React, { FC } from 'react';
import { FlexRow, IconContainer, Text } from '@epam/loveship';
import { ReactComponent as navigation } from '@epam/assets/icons/common/navigation-chevron-right-12.svg';
import { Breadcrumbs } from '../../../api/typings/document';
import { Link } from 'react-router-dom';
import styles from './breadcrumb-navigation.module.scss';

type BreadcrumbNavigationProps = {
    breadcrumbs: Breadcrumbs[];
};

export const BreadcrumbNavigation: FC<BreadcrumbNavigationProps> = ({ breadcrumbs }) => (
    <FlexRow cx={styles.container}>
        {breadcrumbs.map(({ name, url }, index) => (
            <React.Fragment key={name}>
                {index > 0 && <IconContainer icon={navigation} />}
                {url ? (
                    <Link to={url}>
                        <Text cx={styles.activeLink}>{name}</Text>
                    </Link>
                ) : (
                    <Text color="night600">{name}</Text>
                )}
            </React.Fragment>
        ))}
    </FlexRow>
);
