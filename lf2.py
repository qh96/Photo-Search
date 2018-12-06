from __future__ import print_function
import boto3

import json
import requests
from requests_aws4auth import AWS4Auth

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

# ----------------Logic Begin---------------- #
    

def getFromLex(intent_request):
    
    searchKeyA = get_slots(intent_request)["searchKeyA"]
    searchKeyB = get_slots(intent_request)["searchKeyB"]
    return (searchKeyA,searchKeyB)

def responseToLex(intent_request,content):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': content})
        
def getFromES(key1, key2):
    
    if not key2:
        querystr = str(key1)
    else:
        querystr = str(key1) + ' ' + str(key2)
    
    region = 'us-east-1' # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    host = 'vpc-photos-qcbkvhvfytmklvrjybxgp6sjom.us-east-1.es.amazonaws.com' 
    index = 'photos'# index not found exception. Just change photo to photos
    url = 'https://' + host + '/' + index + '/_search'
    print("querystr : " + querystr)
    if querystr == 'all':
        query =  {
            "query": {
                "match_all": {}
            }
        }
    else:
        query = {
           "query":{
              "query_string":{
                 "query":querystr
              }
           }
        }
    # ES 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }

    # Make the signed HTTP request
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

    # Create the response and add some extra content to support CORS
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    # Add the search results to the response
    response['body'] = r.text
    return response

def parseHits(tup):
    searchKeyA,searchKeyB = tup[0],tup[1]
    response = getFromES(searchKeyA, searchKeyB)
    js = json.loads(response['body'])
    try:
        # TODO: write code...
        hits = []
        for i in range(len(js['hits']['hits'])):
            hits.append(js['hits']['hits'][i]['_source']['objectKey'])
        return hits
    except Exception, e:
        return 'no_photo_found'
    

# Lambda execution starts here
def lambda_handler(event, context):
    tup = getFromLex(event)
    fileUrls = ""
    string = ""
    hitsList = parseHits(tup)
    # print(hitsList)
    if not hitsList:
        return responseToLex(event,"no_photo_found")
    for i in range(len(hitsList)):
        string = "https://s3.amazonaws.com/s3ccphoto/" + hitsList[i] + "$"
        fileUrls += string
    
    return responseToLex(event,fileUrls)