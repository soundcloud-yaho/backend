#!/bin/bash
set -euo pipefail

: "${DB_PASSWORD:?DB_PASSWORD 환경변수가 필요합니다.}"

WRITER_ENDPOINT=$(terraform output -raw aurora_writer_endpoint)
READER_ENDPOINT=$(terraform output -raw aurora_reader_endpoint)
DB_NAME=$(terraform output -raw database_name)
DB_PORT=$(terraform output -raw db_port)
DB_USER=$(terraform output -raw master_username)

kubectl create secret generic backend-db-secret \
  --from-literal="DB_WRITER_HOST=${WRITER_ENDPOINT}" \
  --from-literal="DB_READER_HOST=${READER_ENDPOINT}" \
  --from-literal="DB_PORT=${DB_PORT}" \
  --from-literal="DB_NAME=${DB_NAME}" \
  --from-literal="DB_USER=${DB_USER}" \
  --from-literal="DB_PASSWORD=${DB_PASSWORD}" \
  --dry-run=client \
  -o yaml |
kubectl apply -f -