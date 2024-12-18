FROM amazon/aws-lambda-python:latest

RUN pip install boto3 aws_lambda_powertools

COPY ./s3store-lambda/main.py /var/task/lambda_function.py

CMD [ "lambda_function.handle_request" ]

