import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Annotation } from './typings';
import { Link } from '../../../api/typings';
import { useTaskAnnotatorContext } from '../../../connectors/task-annotator-connector/task-annotator-context';
import { getPointsForLinks, PointSet } from './utils/get-points-for-link';
import { LinkAnnotation } from './components/link-annotation';

interface LinksLayerProps {
    scale: number;
    pageNum: number;
    annotations: Annotation[];
}

export const LinksLayer = ({ annotations, pageNum, scale }: LinksLayerProps) => {
    const { onLinkDeleted, onSplitLinkSelected, categories } = useTaskAnnotatorContext();
    const [pointSets, setPointSets] = useState<PointSet[]>([]);

    const annotationsById = useMemo(
        () =>
            annotations.reduce((acc: Record<string, Annotation>, annotation) => {
                acc[annotation.id] = annotation;
                return acc;
            }, {}),
        [annotations]
    );

    const onDeleteLink = useCallback(
        (pageNum: number, from: string | number, link: Link) => (e: Event) => {
            e.stopPropagation();
            onLinkDeleted(pageNum, from, link);
        },
        [onLinkDeleted]
    );

    const onLinkSelect = useCallback(
        (from: string | number, link: Link, annotations: Annotation[]) => () => {
            onSplitLinkSelected(from, link, annotations);
        },
        [onSplitLinkSelected]
    );

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
                    categories
                )
            );
        }
        setPointSets(newPointSets);
    }, [annotations, pageNum, categories, scale]);

    return (
        <div>
            {pointSets.map(({ from, start, finish, category, type, link }) => {
                return (
                    <LinkAnnotation
                        key={`${from}${link.to}`}
                        pointStart={start}
                        pointFinish={finish}
                        category={category}
                        linkType={type}
                        reversed={finish.id === from}
                        onDeleteLink={onDeleteLink(pageNum, from, link)}
                        onLinkSelect={onLinkSelect(from, link, annotations)}
                    />
                );
            })}
        </div>
    );
};
