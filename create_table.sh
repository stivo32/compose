#!/bin/sh

echo "Ожидание запуска DynamoDB..."
until curl -s http://dynamodb:8000 > /dev/null; do
  echo "Ожидание базы данных..."
  sleep 5
done

aws dynamodb create-table \
    --table-name newsletter \
    --attribute-definitions \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=email,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --table-class STANDARD --endpoint-url http://dynamodb:8000