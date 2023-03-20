import React, { CSSProperties, FC, useMemo } from 'react';
import { Point, AnnotationBoundType, PageToken, AnnotationImageToolType } from '../../typings';
import { BoxSelection } from '../../components/box-selection/box-selection';
import { getRectFrom2Points } from '../../utils/get-rect-from-2-points';
import { TextAnnotation as TextSelection } from '../../components/text-annotation';
import { AnnotationLinksBoundType } from 'shared';

type MultilineTextProps = {
    tokens: PageToken[];
    scale: number;
    color: string;
    label: string;
};

type SelectionLayerProps = {
    selectionType:
        | string
        | AnnotationBoundType
        | AnnotationLinksBoundType
        | AnnotationImageToolType;
    selectionCoords: Point[];
    selectionStyle?: CSSProperties;
    isSelectionEnded: boolean;
    multilineTextProps: MultilineTextProps;
    page: number;
};

export const SelectionLayer: FC<SelectionLayerProps> = ({
    selectionStyle,
    selectionType = 'box',
    selectionCoords,
    isSelectionEnded,
    multilineTextProps,
    page
}) => {
    if (!selectionCoords || isSelectionEnded) return null;

    const drawSelection = useMemo(() => {
        if (['box', 'free-box', 'table'].includes(selectionType) && selectionCoords.length === 2) {
            const selectionRect = getRectFrom2Points(selectionCoords[0], selectionCoords[1]);
            return <BoxSelection selectionStyle={selectionStyle} selectionRect={selectionRect} />;
        }
        if (selectionType === 'text' && selectionCoords.length === 2) {
            return (
                <TextSelection
                    scale={multilineTextProps.scale}
                    tokens={multilineTextProps.tokens}
                    color={multilineTextProps.color}
                    label={multilineTextProps.label}
                    page={page}
                    labels={[{ label: multilineTextProps.label }]}
                />
            );
        }
    }, [selectionCoords]);

    return <div>{drawSelection}</div>;
};
