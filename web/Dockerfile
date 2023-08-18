FROM node:18 as build
WORKDIR /usr/build

COPY . ./
COPY .env.development .env

RUN rm .env.* \
    && yarn && npm install -g serve \
    && yarn build && yarn global add serve

CMD serve -s build
EXPOSE 3000
