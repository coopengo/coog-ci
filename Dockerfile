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
    && rm -rf ~/.ssh

WORKDIR "/customers"

RUN git checkout $CUSTOMER-coog-$VERSION_TAG \
    && mv modules/* /workspace/coog/modules \
    && rm -rf /customers \
    && ep link
