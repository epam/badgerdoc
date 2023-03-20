import { ReactElement } from 'react';
import { render, queries, RenderOptions } from '@testing-library/react';
import * as queriesById from './queriesById';

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, 'queries'>) =>
    render(ui, {
        queries: { ...queries, ...queriesById },
        ...options
    });

export * from '@testing-library/react';
export { customRender as render };
