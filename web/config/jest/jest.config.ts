const rootDir = '../../';

const config = {
    rootDir,
    preset: 'ts-jest',
    verbose: true,
    testEnvironment: 'jsdom',
    moduleNameMapper: {
        '\\.scss$': '<rootDir>/node_modules/jest-css-modules',
        '\\.svg$': '<rootDir>/config/jest/__mocks__/svg.ts'
    },
    setupFilesAfterEnv: ['@testing-library/jest-dom/extend-expect']
};

export default config;
