import { EpamColor, IconButton } from '@epam/loveship';
import React, { CSSProperties, useMemo } from 'react';
import { getStyledLinkByBounds, LinkAnnotationProps } from './helpers';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { ReactComponent as ArrowIcon } from '@epam/assets/icons/common/navigation-arrow-down-24.svg';

import styles from './link-annotation.module.scss';

export const LinkAnnotation = ({
    pointStart,
    pointFinish,
    category,
    linkType,
    onDeleteLink,
    reversed
}: LinkAnnotationProps) => {
    const getStyleFromLink = useMemo(() => {
        return {
            ...getStyledLinkByBounds(pointStart, pointFinish),
            height: '1px',
            background:
                linkType == 'directional'
                    ? `${category.metadata?.color}`
                    : ` linear-gradient(90deg, ${category.metadata?.color}, ${category.metadata?.color} 75%, transparent 75%, transparent 100%)`,
            backgroundPosition: 'bottom',
            backgroundSize: '15px',
            backgroundRepeat: 'repeat-x',
            position: 'absolute',
            transformOrigin: 'left'
        };
    }, [pointStart, pointFinish]);

    return (
        <div style={getStyleFromLink as CSSProperties} className={styles.link}>
            <div className={styles.container} style={{ color: category.metadata?.color }}>
                <div
                    className={styles.arrowBottom}
                    style={{ visibility: !reversed ? 'hidden' : undefined }}
                >
                    <ArrowIcon />
                </div>
                <div className={styles.label}>
                    <IconButton
                        icon={closeIcon}
                        onClick={onDeleteLink}
                        color={category.metadata?.color as EpamColor}
                        iconPosition={'right'}
                    />
                </div>
                <div
                    className={styles.arrowTop}
                    style={{ visibility: reversed ? 'hidden' : undefined }}
                >
                    <ArrowIcon />
                </div>
            </div>
        </div>
    );
};
