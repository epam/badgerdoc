import React from 'react';
import { createRoot } from 'react-dom/client';
import { Router } from 'react-router-dom';
import { createBrowserHistory } from 'history';
import { Snackbar, Modals } from '@epam/uui-components';
import { ErrorHandler } from '@epam/loveship';
import './shared/helpers/styles/index.scss';
import '@epam/uui-components/styles.css';
import '@epam/loveship/styles.css';
import { App } from 'App';
import { svc } from 'services';

import { QueryClient, QueryClientProvider } from 'react-query';
import { ContextProvider } from '@epam/uui';

const history = createBrowserHistory();
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: process.env.NODE_ENV === 'production'
        }
    }
});

const UuiEnhancedApp = () => (
    <ContextProvider
        onInitCompleted={(context) => {
            Object.assign(svc, context);
        }}
        history={history}
    >
        <QueryClientProvider client={queryClient}>
            <ErrorHandler>
                <App />
                <Snackbar />
                <Modals />
            </ErrorHandler>
        </QueryClientProvider>
    </ContextProvider>
);

const RoutedApp = () => (
    <Router history={history}>
        <UuiEnhancedApp />
    </Router>
);

createRoot(document.getElementById('root')!).render(<RoutedApp />);
