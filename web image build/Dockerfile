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
RUN ls

# Clone private repository
RUN --mount=type=ssh git clone --single-branch --branch ${CUSTOMER}-coog-${VERSION_TAG} git@github.com:coopengo/customers.git

WORKDIR /web/customers

RUN git checkout $CUSTOMER-coog-$VERSION_TAG

# # Add symbolic links
RUN ep link

VOLUME ["/web/coog-app"]
ENTRYPOINT ["ep"]
EXPOSE 3000
