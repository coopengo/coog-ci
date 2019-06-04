# syntax=docker/dockerfile:experimental

FROM coopengo/coog:master-latest

ARG CUSTOMER
ARG VERSION_TAG

# Install ssh client and git
RUN apk add --no-cache openssh-client git

# Download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Clone private repository
RUN --mount=type=ssh git clone --single-branch --branch $CUSTOMER-coog-2.0 git@github.com:coopengo/customers.git

#RUN git -b checkout $VERSION_TAG

RUN mv customers/modules/* /workspace/coog/modules \
    && rm -rf customers

# Add symbolic links
RUN ep link
