module.exports = {
    root: true, // Make sure eslint picks up the config at the root of the directory
    parser: '@typescript-eslint/parser',
    parserOptions: {
        ecmaVersion: 2020, // Use the latest ecmascript standard
        sourceType: 'module', // Allows using import/export statements
        ecmaFeatures: {
            jsx: true // Enable JSX since we're using React
        }
    },
    settings: {
        react: {
            version: 'detect' // Automatically detect the react version
        }
    },
    env: {
        browser: true, // Enables browser globals like window and document
        amd: true, // Enables require() and define() as global variables as per the amd spec.
        node: true, // Enables Node.js global variables and Node.js scoping.
        mocha: true,
        jest: true
    },
    plugins: ['@typescript-eslint'],
    extends: [
        'eslint:recommended',
        'plugin:react/recommended',
        'plugin:jsx-a11y/recommended',
        'plugin:prettier/recommended' // Make this the last element so prettier config overrides other formatting rules
    ],
    rules: {
        'prettier/prettier': ['warn', {}, { usePrettierrc: true }], // Use our .prettierrc file as source
        'no-unused-vars': 'off',
        '@typescript-eslint/no-unused-vars': 1,
        'no-debugger': 1,
        'jsx-a11y/no-static-element-interactions': 1,
        'react/prop-types': [2, { ignore: ['children'] }]
    }
};
