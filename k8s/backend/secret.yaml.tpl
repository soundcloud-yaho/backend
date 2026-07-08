# secret.yaml

apiVersion: v1
kind: Secret
metadata:
  name: football-secret
type: Opaque
stringData:
  DB_USER: postgres
  DB_PASSWORD: password
  DB_WRITER_HOST: #????
  DB_READER_HOST: #????
  FOOTBALL_DATA_API_KEY: "849ede26d4d84d96aecb7757457a042e"