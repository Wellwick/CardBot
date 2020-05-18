import pickle, os.path, datetime, random, difflib
from googleapiclient.discovery import build
from google.oauth2 import service_account as s_a

SECRET = os.path.join(os.getcwd(), "gsecret.json")
SCOPES = ['https://www.googleapis.com/auth/drive']

c = s_a.Credentials.from_service_account_file(SECRET, scopes=SCOPES)

service = build('sheets', 'v4', credentials=c)
drive_service = build('drive', 'v3', credentials=c)

# - - - - More weird channel stuff below. Should hopefully still work when copy-pasted

TradingDatabaseID = '1MWxevabC-7OiQuEd8vT6HWsLGxhqTHxkhKOLzLP7Qmk'
ReccID = '1MYxwMMXpNfx22gsbPmKLlkPh30NZNXeKSMBo96s7knc'

async def trading_cards():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=TradingDatabaseID,
                                range='Cards!A2:I1000').execute()
    values = result.get('values', [])
    allinfo = []
    for row in values:
        try:
            if not str(row[0]) == "":
                allinfo += [ row ]
            else:
                break
        except:
            break

    return allinfo

async def owned_cards():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=TradingDatabaseID,
                                range='Owned!A2:B10000').execute()
    values = result.get('values', [])
    allinfo = []
    for row in values:
        try:
            if not str(row[0]) == "":
                allinfo += [ row ]
            else:
                break
        except:
            break

    return allinfo

async def gain_card(claimer, card_index):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=TradingDatabaseID,
                                range='Owned!A2:B10000').execute()
    values = result.get('values', [])
    used_rows = 1
    for row in values:
        try:
            if not str(row[0]) == "":
                used_rows += 1
            else:
                break
        except:
            break

    data_to_paste = '<table><tr><td>' + claimer + \
                          '</td><td>' + str(card_index) + '</tr></table>'

    paste_req = {
        "pasteData": {
            "coordinate": {
                "sheetId": 1573195804,
                "rowIndex": used_rows,
                "columnIndex": 0
            },
            "data": data_to_paste,
            "type": "PASTE_VALUES",
            "html": True
        }
    }
    reqs = [paste_req]
    batch_res = sheet.batchUpdate(spreadsheetId=TradingDatabaseID, body={"requests": reqs}).execute()
    

async def move_card_owner(old, new, cards):
    if len(cards) == 0:
        return
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=TradingDatabaseID,
                                range='Owned!A2:B10000').execute()
    values = result.get('values', [])
    reqs = []
    for card in cards:
        for row in range(0, len(values)):
            try:
                owner = str(values[row][0])
                c_index = str(values[row][1])
                if owner == old and c_index == str(card):
                    values[row][0] = new
                    reqs += [{
                        "pasteData": {
                            "coordinate": {
                                "sheetId": 1573195804,
                                "rowIndex": row+1,
                                "columnIndex": 0
                            },
                            "data": '<table><tr><td>' + new + '</td></tr></table>',
                            "type": "PASTE_VALUES",
                            "html": True
                        }
                    }]
                    break
            except:
                continue
    
    batch_res = sheet.batchUpdate(spreadsheetId=TradingDatabaseID, body={"requests": reqs}).execute()

async def remove_cards(owner, cards):
    if len(cards) == 0:
        return
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=TradingDatabaseID,
                                range='Owned!A2:B10000').execute()
    values = result.get('values', [])
    rows_to_delete = []
    for card in cards:
        for row in range(0, len(values)):
            try:
                own = str(values[row][0])
                c_index = str(values[row][1])
                if owner == own and c_index == str(card) and not row in rows_to_delete:
                    rows_to_delete += [row]
                    break
            except:
                continue
    
    if len(rows_to_delete) != len(cards):
        return

    # Delete in reverse order!
    rows_to_delete.sort(reverse=True)
    for i in rows_to_delete:
        del_req = {
            "deleteDimension": {
                "range": {
                    "sheetId": 1573195804,
                    "dimension": "ROWS",
                    "startIndex": i+1,
                    "endIndex": i+2
                }
            }
        }
        batch_res = sheet.batchUpdate(spreadsheetId=TradingDatabaseID, body={"requests": [del_req]}).execute()

async def recc_sheet_write(sheet_id, sheet_name, who, recc):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=ReccID,
                                range='{}!A3:G1000'.format(sheet_name)).execute()
    values = result.get('values', [])
    used_rows = 2
    for row in values:
        try:
            if not str(row[0]) == "":
                used_rows += 1
            else:
                break
        except:
            break

    data_to_paste = '<table><tr><td>' + str(recc[0]) + '</td>'
    if len(recc) > 1:
        data_to_paste += '<td>{}</td>'.format(recc[1])
    else:
        data_to_paste += '<td></td>'
    data_to_paste += '<td>{}</td>'.format(who)
    for i in recc[2:]:
        data_to_paste += '<td>{}</td>'.format(i)
    data_to_paste += '</tr></table>'

    paste_req = {
        "pasteData": {
            "coordinate": {
                "sheetId": sheet_id,
                "rowIndex": used_rows,
                "columnIndex": 0
            },
            "data": data_to_paste,
            "type": "PASTE_VALUES",
            "html": True
        }
    }
    reqs = [paste_req]
    batch_res = sheet.batchUpdate(spreadsheetId=ReccID, body={"requests": reqs}).execute()

async def recommend(who, recc):
    await recc_sheet_write(0, "Recs", who, recc)

async def mywork(who, recc):
    await recc_sheet_write(1683188476, "Works", who, recc)
