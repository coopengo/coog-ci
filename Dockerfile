# syntax=docker/dockerfile:experimental

ARG IMPORT

FROM $IMPORT

ARG CUSTOMER
ARG VERSION_TAG
ARG VERSION
ARG CUSTOM_REPOS

# Download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts 

RUN --mount=type=ssh git clone --single-branch --branch $CUSTOMER-coog-$VERSION $CUSTOM_REPOS \
    && cd customers \
    && git checkout $CUSTOMER-coog-$VERSION_TAG \
    && git pull origin \ 
    && cd .. \
    && mkdir workspace/customers \
    && mv customers/modules /workspace/customers/ \
    && rm -rf /customers \
    && rm -rf ~/.ssh \
    && ep link

