#!/bin/bash
#
# The folder from which this code is run should also contain:
#   - A "ssh" folder, with the keys (id_rsa / id_rsa.pub) that can access all
#       the coopengo repository
#   - A "secret" file, which will be sourced, and should define the MAIL_USER
#       and MAIL_PASSWORD environment variable. Those will be necessary for
#       sending the report email
#   - The "run_tests" script, which will be uploaded on the server, and which
#       will be responsible for actually running the tests
#
# Prerequisites for scaleway:
#   - Install golang => sudo apt install golang-go
#   - Set go environment => export GOPATH=$HOME/go; export PATH=$PATH:$GOPATH/bin
#   - Install the cli => go get -u github.com/scaleway/scaleway-cli/cmd/scw
#
# Get some credentials here :
#   https://cloud.scaleway.com/#/credentials
#
# The secret key should be set in the "TOKEN" environment variable before
# running the script
#
# Get the organization ID :
#    https://cloud.scaleway.com/#/account
#
# The organization ID should be set in the "ORG_ID" environment variable
#
# For usage in crontabs, ssh keys should be automatically available by using
# keychain:
#
#   sudo apt install keychain
#   export HOSTNAME=`hostname` # HOSTNAME not set some machines
#
# Add in ~/.profile:
#
#   if [ -x /usr/bin/keychain -a -f $HOME/.keychain/${HOSTNAME}-sh ] ; then
#       /usr/bin/keychain $HOME/.ssh/id_rsa
#       source $HOME/.keychain/${HOSTNAME}-sh
#   fi
#
# Example crontab configuration:
#
#   KEYCHAIN_FILE=/home/{USER}/.keychain/{HOSTNAME}-sh
#   ORG_ID=XXXXXXXXXXXXXXXXXXXXXX
#   TOKEN=XXXXXXXXXXXXXXXXXXXXXX
#   PATH=/home/{USER}/go/bin:/bin:/sbin:/usr/bin:/usr/sbin
#   bash /path/to/test_scaleway.sh > /path/to/tests.log

# Strict mode, we want an error to crash the script
set -euo pipefail

if [ "${KEYCHAIN_FILE:-notset}" = "notset" ]; then
    echo "KEYCHAIN_FILE not set, assuming running from dev env"
else
    echo Loading ssh keys
    source "$KEYCHAIN_FILE"
fi

# Get current dir in case "cd" was not properly done
cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null || exit 1
echo Directory switched to "$(pwd)"

# Default to master
BRANCH="${1:-master}"

# Server size, can be checked with "scw products servers". START1-XS are not ok
# to run with docker
SERVER_TYPE=${SERVER_TYPE:-"X64-15GB"}

# Image name. We want an image with a pre-installed docker :
#   scw images -f name=docker
IMAGE_NAME=Debian_Buster

# Nice name
SERVER_NAME="test-$(date '+%Y%m%d-%H%M%S')"

# Identify test script
if [ "${TEST_APIS:-0}" != "0" ]; then
    TEST_SCRIPT=run_api_tests
else
    TEST_SCRIPT=run_tests
fi

# Login
echo Logging in to scaleway
scw login \
    --skip-ssh-key=true \
    --organization="$ORG_ID" \
    --token="$TOKEN" > /dev/null

# Init an instance
echo Creating instance
SERVER_ID=$(scw create \
    --tmp-ssh-key \
    --commercial-type="$SERVER_TYPE" \
    --name="$SERVER_NAME" \
    "$IMAGE_NAME")

echo ""
echo Target Branch: "$BRANCH"
echo Server Name: "$SERVER_NAME"
echo Server Id: "$SERVER_ID"
echo Starting at: "$(date --iso-8601=seconds)"

function terminate {
    echo Terminating Server
    scw rm -f "$SERVER_ID" > /dev/null
}

if [ "${DISABLE_AUTO_TERMINATE:-notset}" = "notset" ]; then
    trap terminate EXIT
fi

# Start it
echo ""
echo "Starting the server"
scw start --wait --timeout=600 "$SERVER_ID" > /dev/null

# Copy ssh data
echo "Copying git ssh data"
scw cp ssh "$SERVER_ID":/root 2>&1

# Copy test script
echo "Copying test script"
scw cp "$TEST_SCRIPT" "$SERVER_ID:/root" 2>&1
scw cp secrets "$SERVER_ID:/root" 2>&1

# Run script
echo "Starting test run"
echo ""
# For some reason, without this the file won't be found for running
scw exec --wait "$SERVER_ID" 'ls /root' > /dev/null
scw exec --wait "$SERVER_ID" "/root/$TEST_SCRIPT $BRANCH"

# The end
echo ""
echo Finished at: "$(date --iso-8601=seconds)"
echo ""
