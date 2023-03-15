import { TUserShort } from 'api/typings';
import { Annotation } from 'shared';
import { OWNER_TAB } from './constants';

export const getTabs = (users: TUserShort[], userIds: string[]) => {
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

export const getSortedAllAnnotationList = (annotationsByPageNum: Record<string, Annotation[]>) =>
    Object.values(annotationsByPageNum).flat().sort(sortByCoordinates);

export const getSortedAnnotationsByUserId = (annotationsByUserId: Record<string, Annotation[]>) =>
    Object.keys(annotationsByUserId).reduce((accumulator: typeof annotationsByUserId, userId) => {
        accumulator[userId] = annotationsByUserId[userId].sort(sortByCoordinates);
        return accumulator;
    }, {});
