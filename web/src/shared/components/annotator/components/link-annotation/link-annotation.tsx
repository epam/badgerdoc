// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, eqeqeq, react-hooks/exhaustive-deps */
import React, { CSSProperties, useMemo } from 'react';
import { getStyledLinkByBounds, LinkAnnotationProps } from './helpers';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-12.svg';
import { ReactComponent as ArrowIcon } from '@epam/assets/icons/common/media-play-18.svg';
import { EpamColor, IconButton } from '@epam/loveship';

import styles from './link-annotation.module.scss';

export const LinkAnnotation = ({
    pointStart,
    pointFinish,
    category,
    linkType,
    onDeleteLink,
    onLinkSelect,
    reversed,
    color,
    xBound
}: LinkAnnotationProps) => {
    const commonStyles = {
        height: '1px',
        background:
            linkType == 'directional'
                ? `${color}`
                : ` linear-gradient(90deg, ${color}, ${color} 75%, transparent 75%, transparent 100%)`,
        backgroundPosition: 'bottom',
        backgroundSize: '15px',
        backgroundRepeat: 'repeat-x',
        position: 'absolute',
        transformOrigin: 'left'
    };

    const getStyleFromLink = useMemo(() => {
        return {
            ...getStyledLinkByBounds(pointStart, pointFinish),
            ...commonStyles
        };
    }, [pointStart, pointFinish]);

    const getStyleFromLink1 = useMemo(() => {
        return {
            ...getStyledLinkByBounds(
                {
                    ...pointStart,
                    x: pointFinish.x,
                    y: pointFinish.y
                },
                {
                    ...pointFinish,
                    x: xBound
                }
            ),
            ...commonStyles
        };
    }, [pointStart, pointFinish, xBound]);

    const getStyleFromLink2 = useMemo(() => {
        return {
            ...getStyledLinkByBounds(
                {
                    ...pointStart,
                    x: xBound
                },
                {
                    ...pointFinish,
                    x: xBound
                }
            ),
            ...commonStyles
        };
    }, [pointStart, pointFinish, xBound]);

    const getStyleFromLink3 = useMemo(() => {
        return {
            ...getStyledLinkByBounds(pointStart, {
                ...pointFinish,
                x: xBound,
                y: pointStart.y
            }),
            ...commonStyles
        };
    }, [pointStart, pointFinish, xBound]);

    const NewLink = (
        <>
            <div
                style={getStyleFromLink1 as CSSProperties}
                className={styles.link}
                onClick={onLinkSelect}
                role="none"
            >
                <div className={styles.container} style={{ color }}>
                    <div
                        className={`${styles.arrow} ${styles.arrowBottom}`}
                        style={{ visibility: reversed ? 'hidden' : undefined }}
                    >
                        <ArrowIcon />
                    </div>
                </div>
            </div>
            <div
                style={getStyleFromLink2 as CSSProperties}
                className={styles.link}
                onClick={onLinkSelect}
                role="none"
            >
                <div className={styles.container} style={{ color }}>
                    <div className={styles.label}>
                        <IconButton
                            icon={closeIcon}
                            onClick={onDeleteLink}
                            color={color as EpamColor}
                            iconPosition={'right'}
                        />
                    </div>
                </div>
            </div>
            <div
                style={getStyleFromLink3 as CSSProperties}
                className={styles.link}
                onClick={onLinkSelect}
                role="none"
            >
                <div className={styles.container} style={{ color }}>
                    <div
                        className={`${styles.arrow} ${styles.arrowBottom}`}
                        style={{ visibility: !reversed ? 'hidden' : undefined }}
                    >
                        <ArrowIcon />
                    </div>
                </div>
            </div>
        </>
    );

    const OldLink = (
        <div
            style={getStyleFromLink as CSSProperties}
            className={styles.link}
            onClick={onLinkSelect}
            role="none"
        >
            <div className={styles.container} style={{ color: category.metadata?.color }}>
                <div
                    className={`${styles.arrow} ${styles.arrowBottom}`}
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
                    className={styles.arrow}
                    style={{ visibility: reversed ? 'hidden' : undefined }}
                >
                    <ArrowIcon />
                </div>
            </div>
        </div>
    );

    return NewLink;
    // OldLink
};
