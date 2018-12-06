#!/usr/bin/env bash
#
# Accepted parameters are:
#   - BRANCH: The branch which will be used to start the service. Defaults to
#   "master"
#
# The AUTO_TERMINATE environment variable can be set to anything else than "1"
# so that the server stays up once the initialisation is done. The default
# value is to kill it, so that persistency is a consious choice.
#
# The folder from which this code is run should also contain:
#   - A "ssh" folder, with the keys (id_rsa / id_rsa.pub) that can access all
#       the coopengo repository
#   - A "secret" file, which will be sourced, and should define the secret
#       environment variables that will be used to configure the server
#   - The "install_coog" script, which will be uploaded on the server, and which
#       will be responsible for actually installing and configuring the
#       application
#
# Configuration :
#
# pip install awscli
#
# La création des utilisateurs / accès se fait ici :
# https://console.aws.amazon.com/iam/home?#/users
#
# ===> aws configure
#
# ID : xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Clé : xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# region : eu-west-3
# format : text
#
#
# Création du groupe de sécurité (déjà créé, mais si nécessaire d'en faire un
# nouveau)
#
# ===> aws ec2 create-security-group --group-name devenv-sg \
#         --description "security group for development environment"
#
# <=== group_id
#
# Group ID : xxxxxxxxxxxxxxxxxxx
#
# Autorisations ssh :
#
# ===> aws ec2 authorize-security-group-ingress --group-name devenv-sg \
#         --protocol tcp --port 22 --cidr 0.0.0.0/0
#
# Création d'une paire de clés pour la connexion (la clé sera stockée dans
# "devenv-key.pem" :
#
# ===> aws ec2 create-key-pair --key-name devenv-key --query 'KeyMaterial' \
#         --output text > devenv-key.pem
# ===> chmod 400 devenv-key.pem

# Strict mode, we want an error to crash the script
set -euo pipefail

BRANCH=${1:-master}
KEY_NAME="devenv-key"
GROUP_ID="sg-XXXXXXXXXXXXXXXXXXXXXXX"
IMAGE_ID="ami-XXXXXXXXXXXXXXXXXXXXXX"  # Debian based for chronic to work properly
INSTANCE_TYPE="m5.large"

# Depends on the ami, either "ubuntu" or "ec2-user"
INSTANCE_USER="ubuntu"

# Auto terminate instance by default to avoid long running servers
AUTO_TERMINATE=${AUTO_TERMINATE:-1}

# Start instance
echo 'Starting instance'
INSTANCE_ID=$(aws ec2 run-instances --image-id "$IMAGE_ID" \
        --security-group-ids "$GROUP_ID" \
        --count 1 --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --query 'Instances[0].InstanceId')
echo "Instance Id: $INSTANCE_ID"

function terminate {
    if [ "$AUTO_TERMINATE" = "1" ]; then
        echo "Terminating instance $INSTANCE_ID"
        aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" \
            || >&2 echo "Error terminating $INSTANCE_ID, you may have to do it manually"
    fi
}
trap terminate EXIT

# Get instance ip
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress')
echo "Instance Ip: $INSTANCE_IP"

sleep 60

echo "Uploading required files"
scp -o StrictHostKeyChecking=no -o ConnectTimeout=300 -i "$KEY_NAME.pem" \
    -r ssh "$INSTANCE_USER"@"$INSTANCE_IP":~/ssh
scp -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" secrets \
    "$INSTANCE_USER"@"$INSTANCE_IP":~/secrets
scp -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" install_coog \
    "$INSTANCE_USER"@"$INSTANCE_IP":~/install_coog

ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP" \
    "sudo su root -c \"cp -r /home/$INSTANCE_USER/ssh /root\""
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP" \
    "sudo su root -c \"cp -r /home/$INSTANCE_USER/secrets /root\""
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP" \
    "sudo su root -c \"cp -r /home/$INSTANCE_USER/install_coog /root\""

echo "Starting up at $(date)"
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP" \
    'bash -s' < prepare_instance

ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP" \
    "sudo su root -c \"bash /root/install_coog $BRANCH\""

echo "Terminating at $(date)"

ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" \
    "$INSTANCE_USER"@"$INSTANCE_IP"
