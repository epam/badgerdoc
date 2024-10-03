// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Annotation } from './typings';
import { Link } from '../../../api/typings';
import { useTaskAnnotatorContext } from '../../../connectors/task-annotator-connector/task-annotator-context';
import { getPointsForLinks, PointSet } from './utils/get-points-for-link';
import { LinkAnnotation } from './components/link-annotation';
import { linksOffsets } from 'shared/constants/annotations';

interface LinksLayerProps {
    scale: number;
    pageNum: number;
    annotations: Annotation[];
}

export const LinksLayer = ({ annotations, pageNum, scale }: LinksLayerProps) => {
    const { onLinkDeleted, onSplitLinkSelected, categories } = useTaskAnnotatorContext();
    const [pointSets, setPointSets] = useState<PointSet[]>([]);
    const [linksSets, setLinksSets] = useState<PointSet[]>([]);

    const annotationsById = useMemo(
        () =>
            annotations.reduce((acc: Record<string, Annotation>, annotation) => {
                acc[annotation.id] = annotation;
                return acc;
            }, {}),
        [annotations]
    );

    const onDeleteLink = useCallback(
        (pageNum: number, annotationId: string | number, link: Link) => (e: Event) => {
            e.stopPropagation();
            onLinkDeleted(pageNum, annotationId, link);
        },
        [onLinkDeleted]
    );

    const onLinkSelect = useCallback(
        (from: string | number, link: Link, annotations: Annotation[]) => () => {
            onSplitLinkSelected(from, link, annotations);
        },
        [onSplitLinkSelected]
    );

    const addXBoundtoPointSet = (points: any[]) => {
        let k = 0;
        const func = (points: any[]) => {
            return points.map((set) => {
                if (k > linksOffsets.length - 1) {
                    k = 0;
                }

                const obj = {
                    xBound: linksOffsets[k],
                    ...set
                };

                ++k;

                return obj;
            });
        };

        return func(points);
    };

    useEffect(() => {
        const newPointSets: PointSet[] = [];
        for (let ann of annotations) {
            if (!ann.links?.length) continue;

            newPointSets.push(
                ...getPointsForLinks(
                    ann.id,
                    ann.boundType,
                    ann.links,
                    pageNum,
                    annotationsById,
                    categories,
                    ann.color
                )
            );
        }
        setPointSets(newPointSets);
    }, [annotations, pageNum, categories, scale]);

    useEffect(() => {
        if (pointSets) {
            const newPointSets = addXBoundtoPointSet(pointSets);
            setLinksSets(newPointSets);
        }
    }, [pointSets]);

    return (
        <div>
            {linksSets.map(
                ({ from, start, finish, category, type, link, color, xBound, annotationId }) => {
                    return (
                        <LinkAnnotation
                            key={`${from}${link.to}`}
                            pointStart={start}
                            pointFinish={finish}
                            category={category}
                            linkType={type}
                            reversed={finish.id === from}
                            onDeleteLink={onDeleteLink(pageNum, annotationId, link)}
                            onLinkSelect={onLinkSelect(from, link, annotations)}
                            color={color}
                            xBound={xBound}
                        />
                    );
                }
            )}
        </div>
    );
};
