import { getSortedAllAnnotationList, getSortedAnnotationsByUserId, getTabs } from '../utils';
import { OWNER_TAB } from '../constants';
import { AnnotationBoundType } from 'shared';

const createAnnotation = (y: number, x: number) => ({
    id: '',
    boundType: 'text' as AnnotationBoundType,
    bound: { y, x, width: 0, height: 0 }
});

describe('getTabs', () => {
    test('Must return proper tabs list', () => {
        const tabs = getTabs({ users: [{ id: '1', username: 'username' }], userIds: ['1'] });

        expect(tabs).toEqual([OWNER_TAB, { id: '1', caption: 'username' }]);
    });
});

describe('getSortedAllAnnotationList', () => {
    test('Must return sorted annotations list for all pages', () => {
        const firstAnnotation = createAnnotation(15, 50);
        const secondAnnotation = createAnnotation(15, 100);
        const thirdAnnotation = createAnnotation(150, 5);
        const annotationsByPageNum = {
            1: [thirdAnnotation, firstAnnotation, secondAnnotation],
            2: [secondAnnotation, thirdAnnotation, firstAnnotation]
        };

        expect(getSortedAllAnnotationList(annotationsByPageNum)).toEqual([
            firstAnnotation,
            secondAnnotation,
            thirdAnnotation,
            firstAnnotation,
            secondAnnotation,
            thirdAnnotation
        ]);
    });
});

describe('getSortedAnnotationsByUserId', () => {
    test('Must return sorted annotations list by userId', () => {
        const firstAnnotation = createAnnotation(15, 50);
        const secondAnnotation = createAnnotation(15, 100);
        const thirdAnnotation = createAnnotation(150, 5);
        const annotationsByPageNum = {
            'user-id': [thirdAnnotation, firstAnnotation, secondAnnotation]
        };

        expect(getSortedAnnotationsByUserId(annotationsByPageNum)).toEqual({
            'user-id': [firstAnnotation, secondAnnotation, thirdAnnotation]
        });
    });
});
