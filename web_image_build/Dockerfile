#syntax=docker/dockerfile:experimental

ARG IMPORT

FROM $IMPORT

ARG CUSTOMER
ARG VERSION_TAG
ARG VERSION

# Download public key for github.cdom
RUN apk add -qU openssh git \
    && mkdir -p -m 0600 ~/.ssh \
    && ssh-keyscan github.com >> ~/.ssh/known_hosts 
    
WORKDIR /web
RUN --mount=type=ssh git clone --single-branch --branch ${CUSTOMER}-coog-${VERSION_TAG} git@github.com:coopengo/customers.git \
    && rm -rf ~/.ssh

WORKDIR /web/customers

RUN git checkout $CUSTOMER-coog-${VERSION}

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
