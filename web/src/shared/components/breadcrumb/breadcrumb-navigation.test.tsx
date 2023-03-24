import React from 'react';
import { render } from '@testing-library/react';
import { BreadcrumbNavigation } from './breadcrumb-navigation';

const breadcrumbMock = [
    { name: 'first element', url: 'url' },
    { name: 'second element', url: 'url2' }
];

describe('BreadcrumbNavigation', () => {
    it('should exist url and name', async () => {
        const { getByText, getAllByRole } = render(
            <BreadcrumbNavigation breadcrumbs={breadcrumbMock} />
        );

        const firstElement = getByText('first element');
        const [firstLink] = getAllByRole('link');

        expect(firstElement).toBeVisible();
        expect(firstLink.getAttribute('href')).toBe('/url');
    });
});
