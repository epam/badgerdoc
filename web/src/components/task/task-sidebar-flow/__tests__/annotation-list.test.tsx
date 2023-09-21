import React from 'react';
import { render } from 'shared/helpers/testUtils/render';
import { AnnotationBoundType } from 'shared';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { stringToRGBA } from 'shared/components/annotator/utils/string-to-rgba';
import { AnnotationList } from '../annotation-list';

window.HTMLElement.prototype.scrollIntoView = function () {};

const createAnnotation = (id: string, label: string, categoryName: string, color: string) => ({
    id,
    label,
    categoryName,
    color,
    boundType: 'text' as AnnotationBoundType,
    bound: { y: 0, x: 0, width: 0, height: 0 }
});

describe('AnnotationList', () => {
    const firstAnnotation = createAnnotation(
        'first',
        'categoryName.annotationLabel',
        'categoryName',
        '#AAAAA'
    );
    const secondAnnotation = createAnnotation('second', 'categoryName', 'categoryName', '#FFFFF');
    const props = {
        list: [firstAnnotation, secondAnnotation],
        selectedAnnotation: firstAnnotation,
        onSelect: () => {},
        isEditable: false
    };

    it('Must select another annotation if selectedAnnotationId is changed', () => {
        const firstAnnotationRowId = `${ANNOTATION_FLOW_ITEM_ID_PREFIX}${firstAnnotation.id}`;
        const secondAnnotationRowId = `${ANNOTATION_FLOW_ITEM_ID_PREFIX}${secondAnnotation.id}`;

        const { rerender, getByText, getByTestId, getById } = render(<AnnotationList {...props} />);

        expect(getByTestId('flow-prev-button').getAttribute('aria-disabled')).toBe('true');
        expect(getByTestId('flow-next-button').getAttribute('aria-disabled')).toBe('false');
        expect(getByText('1 of 2')).toBeVisible();
        expect(getById(firstAnnotationRowId)).toHaveStyle({
            backgroundColor: stringToRGBA(firstAnnotation.color, 0.2)
        });
        expect(getById(secondAnnotationRowId)).toHaveStyle({
            backgroundColor: 'unset'
        });

        rerender(<AnnotationList {...props} selectedAnnotation={secondAnnotation} />);

        expect(getByTestId('flow-prev-button').getAttribute('aria-disabled')).toBe('false');
        expect(getByTestId('flow-next-button').getAttribute('aria-disabled')).toBe('true');
        expect(getByText('2 of 2')).toBeVisible();
        expect(getById(firstAnnotationRowId)).toHaveStyle({
            backgroundColor: 'unset'
        });
        expect(getById(secondAnnotationRowId)).toHaveStyle({
            backgroundColor: stringToRGBA(secondAnnotation.color, 0.2)
        });
    });
});
