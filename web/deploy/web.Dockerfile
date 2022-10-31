FROM node:14
WORKDIR /usr/build
COPY . ./
COPY ./.env.production .env
RUN yarn && npm install -g serve
RUN yarn build && yarn global add serve
EXPOSE 8080
CMD serve -s build
