# syntax=docker/dockerfile:experimental

ARG IMPORT

FROM $IMPORT

ARG CUSTOMER
ARG VERSION_TAG
ARG VERSION

# Download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Clone private repository
RUN --mount=type=ssh git clone --single-branch --branch $CUSTOMER-coog-$VERSION git@github.com:coopengo/customers.git

WORKDIR "/customers"

RUN git checkout $CUSTOMER-coog-$VERSION_TAG

RUN mv modules/* /workspace/coog/modules \
    && rm -rf /customers

# Add symbolic links
RUN ep link
