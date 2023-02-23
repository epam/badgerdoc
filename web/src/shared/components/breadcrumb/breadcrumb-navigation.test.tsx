import React from 'react';
import { render, screen } from '@testing-library/react';

import withRouter from '../../../../config/jest/decorators/withRouter';
import { BreadcrumbNavigation } from './breadcrumb-navigation';

const breadcrumbMock = [
    { name: 'name breadcrumb', url: 'url' },
    { name: 'name 2', url: 'url2' }
];

describe('BreadcrumbNavigation', () => {
    it('should exist url and name', () => {
        render(withRouter(<BreadcrumbNavigation breadcrumbs={breadcrumbMock} />));

        const links = screen.getAllByRole('link');
        const name = screen.getByText('name breadcrumb');

        expect(name).toBeVisible();
        expect(links[0].getAttribute('href')).toBe('/url');
    });
});
