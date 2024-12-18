FROM amazon/aws-lambda-python:latest

RUN pip install boto3

COPY ./newsletter-lambda/main.py /var/task/lambda_function.py

CMD [ "lambda_function.handle_request" ]

