#syntax=docker/dockerfile:experimental

ARG IMPORT

FROM $IMPORT

ARG CUSTOMER
ARG VERSION_TAG
ARG VERSION


RUN apk add openssh git

# Download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh 
RUN ssh-keyscan github.com >> ~/.ssh/known_hosts

WORKDIR /web

# Clone private repository
RUN --mount=type=ssh git clone --single-branch --branch ${CUSTOMER}-coog-${VERSION_TAG} git@github.com:coopengo/customers.git

WORKDIR /web/customers

RUN git checkout $CUSTOMER-coog-${VERSION}

RUN ls /
RUN ls /web
RUN ls /web/customers

WORKDIR /web/coog-api

RUN apk add --no-cache --virtual .build-deps wget ca-certificates make gcc g++ python linux-headers musl-dev \
    && npm i --production \
    && npm cache clean --force \
    && rm -rf /root/.node-gyp \
    && apk del .build-deps

# # Add symbolic links
RUN ep link

VOLUME ["/web/coog-app"]
ENTRYPOINT ["ep"]
EXPOSE 3000
