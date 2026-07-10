#!/bin/bash
set -e

DB_PASSWORD="${DB_PASSWORD:-postgres}"

WRITER_ENDPOINT=$(terraform output -raw aurora_writer_endpoint)
READER_ENDPOINT=$(terraform output -raw aurora_reader_endpoint)
DB_NAME=$(terraform output -raw database_name)
DB_PORT=$(terraform output -raw db_port)
DB_USER=$(terraform output -raw master_username)

kubectl delete secret backend-db-secret --ignore-not-found

kubectl create secret generic backend-db-secret \
  WRITABLE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${WRITER_ENDPOINT}:${DB_PORT}/${DB_NAME}" \
  READONLY_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${READER_ENDPOINT}:${DB_PORT}/${DB_NAME}"