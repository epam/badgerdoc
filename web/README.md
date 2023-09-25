# Getting started

## Required software

-   `node` 8.12.0 or higher (https://nodejs.org/en/)
-   `yarn` package manager (https://yarnpkg.com/en/).
    -   Please note that `npm` is not applicable for installing or building the application.

## Install

```
git clone git@github.com:epam/badgerdoc.git
cd badgerdoc/web
yarn
```

## Available Scripts

### `yarn start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### `yarn test`

Launches the test runner in the interactive watch mode.

See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

## Local Development

To work in local environment you need to start up the **_local backend_** and configure env variables for correct connection.
For that you need to copy content of `.env.example` file to `.env.local` and specify provided variables.
