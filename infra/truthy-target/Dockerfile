FROM node:14-alpine
COPY apks /tmp/apks
RUN apk add --no-network --allow-untrusted /tmp/apks/*.apk && rm -rf /tmp/apks
WORKDIR /usr/src/app
COPY src/package.json src/yarn.lock ./
RUN yarn install
COPY src/ .
RUN yarn build
CMD ["node", "dist/main"]
