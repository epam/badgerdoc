import React from 'react';
import { render } from '@testing-library/react';
import { BreadcrumbNavigation } from './breadcrumb-navigation';
import withRouter from '../../../../config/jest/decorators/withRouter';

const breadcrumbMock = [
    { name: 'first element', url: 'url' },
    { name: 'second element', url: 'url2' }
];

describe('BreadcrumbNavigation', () => {
    it('should exist url and name', async () => {
        const { getByText, getAllByRole } = render(
            withRouter(<BreadcrumbNavigation breadcrumbs={breadcrumbMock} />)
        );

        const firstElement = getByText('first element');
        const [firstLink] = getAllByRole('link');

        expect(firstElement).toBeVisible();
        expect(firstLink.getAttribute('href')).toBe('/url');
    });
});
