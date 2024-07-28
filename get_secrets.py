import os
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.institutions_search_request import InstitutionsSearchRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

############ Load secrets from .env file ###############
# Should contain:
#   PLAID_CLIENT_ID = 'your_client_id'
#   PLAID_SECRET = 'your_secret'
#
# For SMTP email configuration the .env should have:
#   SMTP_SERVER = 'smtp.example.com'
#   SMTP_PORT = 587
#   SMTP_USERNAME = 'sender@example.com'
#   SMTP_PASSWORD = 'example_password'
#   EMAIL_FROM = 'sender@example.com'
#   EMAIL_TO = 'receiver@example.com'


from dotenv import load_dotenv
load_dotenv()

########################################################

############# Plaid API Config #########################
# Need to make account at Plaid API dashboard: https://dashboard.plaid.com/
# This is how get PLAID_CLIENT_ID and PLAID_SECRET

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')

print(type(PLAID_CLIENT_ID))
print(type(PLAID_SECRET))


config = plaid.Configuration(
    host=plaid.Environment.Sandbox,  # or Environment.Development or Environment.Production
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
client = plaid_api.PlaidApi(plaid.ApiClient(config))
########################################################

############# Institution name query ###################
# Param: insitution name i.e FROST
# Returns: institution id (used for getting public token)

institution = 'FROST'

request = InstitutionsSearchRequest(
    query=institution, 
    products=[Products('transactions')],
    country_codes=[CountryCode('US')],
)
response = client.institutions_search(request)
institution_id = response['institution_id']
#########################################################

############### Getting Public Token ####################
request = SandboxPublicTokenCreateRequest(
    institution_id=institution_id,
    initial_products=[Products('transactions')]
)
response = client.sandbox_public_token_create(request)
sandbox_public_token = response['public_token'] 

exchange_request = ItemPublicTokenExchangeRequest(
    public_token=sandbox_public_token
)
exchange_response = client.item_public_token_exchange(exchange_request)
print(exchange_request)

public_token = exchange_request.public_token
#########################################################

################# Getting Access Token ##################
# Put access_token into .env file as ACCESS_TOKEN

request = ItemPublicTokenExchangeRequest(public_token=public_token)
response = client.item_public_token_exchange(request)
access_token = response['access_token']
item_id = response['item_id']

print(item_id)
print(access_token)

#########################################################

