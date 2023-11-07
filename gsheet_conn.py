import json
import pygsheets
from google.oauth2 import service_account

def gsheet_connection():
    SCOPES = ('https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform')
    json_gsheet = open("google_auth.json").read()
    json_key_gsheet = json.loads(json_gsheet,strict=False)
    gsheet_credentials = service_account.Credentials.from_service_account_info(json_key_gsheet,scopes=SCOPES)
    return pygsheets.authorize(custom_credentials=gsheet_credentials)

def read_gsheet(gc, gsheet, worksheet):
    sheet = gc.open_by_url(gsheet).worksheet_by_title(worksheet)
    df= sheet.get_as_df(start='A1', end='38,16', has_header=True, index_colum=None, numerize=True, empty_value='', include_tailing_empty_rows=True)
    df.drop([''], axis='columns', inplace=True, errors='ignore')
    return sheet, df