import { AnnotationsByUserObj } from 'api/hooks/annotations';
import { Category, Label, TUserShort } from 'api/typings';
import { Annotation } from 'shared';
import { OWNER_TAB } from './constants';

export const getTabs = ({ users, userIds }: { userIds: string[]; users: TUserShort[] }) => {
    const userTabs = userIds.map((userId) => {
        const user = users.find(({ id }) => id === userId);

        return { id: userId, caption: user?.username };
    });

    return [OWNER_TAB, ...userTabs];
};

const sortByCoordinates = (first: Annotation, second: Annotation) =>
    first.bound.y === second.bound.y
        ? first.bound.x - second.bound.x
        : first.bound.y - second.bound.y;

export const getSortedAllAnnotationList = (annotationsByPageNum: Record<string, Annotation[]>) => {
    return Object.keys(annotationsByPageNum).reduce((sortedAnnotations: Annotation[], key) => {
        const list = [...annotationsByPageNum[key]].sort(sortByCoordinates);
        sortedAnnotations.push(...list);
        return sortedAnnotations;
    }, []);
};

export const getSortedAnnotationsByUserId = (annotationsByUserId: Record<string, Annotation[]>) =>
    Object.keys(annotationsByUserId).reduce((accumulator: typeof annotationsByUserId, userId) => {
        accumulator[userId] = [...annotationsByUserId[userId]].sort(sortByCoordinates);
        return accumulator;
    }, {});

type TCollectIncomingLinksReturnValue = {
    incomingLinksByAnnotationId: Record<string, Annotation['links']>;
    annotationNameById: Record<string, string>;
};

export const collectIncomingLinks = (annotations: Annotation[]) => {
    return annotations.reduce(
        (acc: TCollectIncomingLinksReturnValue, annotation) => {
            acc.annotationNameById[annotation.id] = annotation.label ?? '';

            annotation.links?.forEach(({ to, ...link }) => {
                if (!acc.incomingLinksByAnnotationId[to]) acc.incomingLinksByAnnotationId[to] = [];

                acc.incomingLinksByAnnotationId[to]?.push({ ...link, to: annotation.id });
            });

            return acc;
        },
        { incomingLinksByAnnotationId: {}, annotationNameById: {} }
    );
};

export const getCategoriesByUserId = (
    userPages: AnnotationsByUserObj[],
    categories?: Category[]
): Record<string, Label[]> => {
    if (!categories?.length) return {};

    return userPages.reduce(
        (acc: Record<string, Label[]>, { user_id, categories: categoriesId }) => ({
            ...acc,
            [user_id]: categoriesId.reduce((labels: Label[], categoryId) => {
                const category = categories.find(({ id }) => id === categoryId);

                if (category) {
                    labels.push({ id: category.id, name: category.name });
                }

                return labels;
            }, [])
        }),
        {}
    );
};
