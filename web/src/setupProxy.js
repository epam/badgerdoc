const morgan = require('morgan');
const { createProxyMiddleware } = require('http-proxy-middleware');
const applyMocks = require('./api/mocks/apply-mocks');

const {
    REACT_APP_FILEMANAGEMENT_API_NAMESPACE,
    REACT_APP_JOBMANAGER_API_NAMESPACE,
    REACT_APP_PIPELINES_API_NAMESPACE,
    REACT_APP_AUTH_API_NAMESPACE,
    REACT_APP_CATEGORIES_API_NAMESPACE,
    REACT_APP_TOKENS_API_NAMESPACE,
    REACT_APP_USERS_API_NAMESPACE,
    REACT_APP_MODELS_API_NAMESPACE,
    REACT_APP_SEARCH_API_NAMESPACE,
    REACT_APP_TAXONOMIES_API_NAMESPACE
} = process.env;

const filemanagementProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_FILEMANAGEMENT_API,
    changeOrigin: true,
    autoRewrite: true
});

const jobsManagerProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_JOB_API,
    changeOrigin: true
});

const pipelinesManagerProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_PIPELINES_API,
    changeOrigin: true
});

const categoriesManagerProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_CATEGORIES_API,
    changeOrigin: true
});

const tokensManagerProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_TOKENS_API,
    changeOrigin: true
});

const authProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_AUTH_API,
    changeOrigin: true
});

const usersProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_USERS_API,
    changeOrigin: true
});

const modelsProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_MODELS_API,
    changeOrigin: true
});

const searchProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_MODELS_API,
    changeOrigin: true
});

const taxonomiesProxyMiddleware = createProxyMiddleware({
    target: process.env.REACT_APP_TAXONOMIES_API,
    changeOrigin: true
});

module.exports = (app) => {
    app.use(applyMocks);
    app.use(REACT_APP_AUTH_API_NAMESPACE, authProxyMiddleware);
    app.use(REACT_APP_FILEMANAGEMENT_API_NAMESPACE, filemanagementProxyMiddleware);
    app.use(REACT_APP_JOBMANAGER_API_NAMESPACE, jobsManagerProxyMiddleware);
    app.use(REACT_APP_PIPELINES_API_NAMESPACE, pipelinesManagerProxyMiddleware);
    app.use(REACT_APP_CATEGORIES_API_NAMESPACE, categoriesManagerProxyMiddleware);
    app.use(REACT_APP_TOKENS_API_NAMESPACE, tokensManagerProxyMiddleware);
    app.use(REACT_APP_USERS_API_NAMESPACE, usersProxyMiddleware);
    app.use(REACT_APP_MODELS_API_NAMESPACE, modelsProxyMiddleware);
    app.use(REACT_APP_SEARCH_API_NAMESPACE, searchProxyMiddleware);
    app.use(REACT_APP_TAXONOMIES_API_NAMESPACE, taxonomiesProxyMiddleware);

    app.use(morgan('combined'));
};
