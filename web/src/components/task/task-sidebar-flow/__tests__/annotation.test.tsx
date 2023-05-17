import React from 'react';
import { render } from 'shared/helpers/testUtils/render';
import { AnnotationRow } from '../annotationRow';
import { AnnotationBoundType } from 'shared';
import { ANNOTATION_PATH_SEPARATOR } from '../constants';
import { ANNOTATION_FLOW_ITEM_ID_PREFIX } from 'shared/constants/annotations';
import { stringToRGBA } from 'shared/components/annotator/utils/string-to-rgba';

describe('AnnotationRow', () => {
    const props = {
        id: '1',
        color: '#AAAAA',
        label: 'firstTaxonomy.lastTaxonomy',
        text: 'Some selected text',
        index: 15,
        onSelect: () => {},
        isEditable: false,
        onSelectById: () => {},
        onLinkDeleted: () => {},
        onCloseIconClick: () => {},
        annotationNameById: {},
        categoryName: 'categoryName',
        selectedAnnotationId: '1',
        boundType: 'text' as AnnotationBoundType,
        bound: { y: 10, x: 100, width: 0, height: 0 }
    };
    it('Must render annotation with full path', () => {
        const { getByText, getByTestId } = render(<AnnotationRow {...props} />);

        const path = getByTestId('flow-path');
        const text = getByText(props.text);
        const label = getByTestId('flow-label');

        expect(path.textContent).toBe(
            `categoryName ${ANNOTATION_PATH_SEPARATOR} firstTaxonomy ${ANNOTATION_PATH_SEPARATOR} lastTaxonomy`
        );
        expect(text).toBeVisible();
        expect(label).toBeVisible();
    });
    it('Must render annotation label with proper color', () => {
        const { getById, rerender } = render(<AnnotationRow {...props} />);

        const rowContainer = getById(`${ANNOTATION_FLOW_ITEM_ID_PREFIX}${props.id}`);

        expect(rowContainer.childNodes[0]).toHaveStyle({
            color: props.color,
            border: `1px solid ${props.color}`,
            backgroundColor: stringToRGBA(props.color, 0.2)
        });

        rerender(<AnnotationRow {...props} selectedAnnotationId="2" />);

        expect(rowContainer.childNodes[0]).toHaveStyle({
            backgroundColor: 'unset'
        });
    });
});
