from __future__ import print_function
import json
import boto3
import datetime
import requests
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    
    fileName = event['Records'][0]['s3']['object']['key']
    # fileName='mybeach.jpg'
    bucket='s3ccphoto'
    
    client=boto3.client('rekognition')

    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':fileName}})
    
    labelArr = []
    
    lenResponse = len(response['Labels'])
    
    for i in range(lenResponse):
        labelArr.append(response['Labels'][i]['Name'])
    
    res = {
        "objectKey" : fileName,
        "bucket" : bucket,
        "createdTimestamp" : str(datetime.datetime.now()),
        "labels" : labelArr
    }
    
    region = 'us-east-1' # e.g. us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    host = 'https://vpc-photos-qcbkvhvfytmklvrjybxgp6sjom.us-east-1.es.amazonaws.com' # the Amazon ES domain, including https://
    index = 'photos'
    type = 'photo'
    url = host + '/' + index + '/' + type

    headers = { "Content-Type": "application/json" }
    
    r = requests.post(url, auth=awsauth, json=res, headers=headers)
    
    print(res)
    return res
