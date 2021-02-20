from ynab_sdk import YNAB
from ynab_sdk.api.models.requests.transaction import TransactionRequest
from datetime import date
import hashlib

def send_transactions(config, bank_config, transactions):
    ynab = YNAB(config.access_token)

    #YNAB doesn't accept future-dated transactions, but ING sometimes produces them
    #just drop them from import until their actual booking date
    transactions = list(filter(lambda t: date.fromisoformat(t.date) <= date.today(),  transactions))

    print(transactions)
    for t in transactions:
        for c in config.clear_memos:
            if c.lower() in t.payee.lower():
                t.memo = None

    transfer_payee_id = ""
    if config.cash_account_id != "":
        cash_account = ynab.accounts.get_account(config.budget_id, config.cash_account_id)
        transfer_payee_id = cash_account.data.account.transfer_payee_id

    def create_request(transaction):
        return TransactionRequest(
            account_id = bank_config.ynab_account_id,
            date = transaction.date,
            amount = transaction.amount,
            memo = transaction.memo[:199] if transaction.memo else None,
            cleared = 'cleared',
            payee_name = None if transaction.cash_withdrawl and transfer_payee_id != "" else transaction.payee,
            payee_id = transfer_payee_id if transaction.cash_withdrawl and transfer_payee_id != "" else None,
            # import_id can only be 36 characters
            import_id = ( "API:" + hashlib.sha256(("%s:%s:%s:%s" % (transaction.payee, transaction.memo, transaction.amount, transaction.date)).encode('utf-8')).hexdigest() )[:36]
        )

    transaction_req = list(map(create_request, transactions))

    response = ynab.transactions.create_transactions(config.budget_id, transaction_req)

    if response:
        if 'error' in response:
            print(f'Account {bank_config.iban}: YNAB import failed with Error: {response}')
        elif 'data' in response:
            if response['data']['duplicate_import_ids']:
                print(f'Account {bank_config.iban}: {len(response["data"]["duplicate_import_ids"])} duplicate transations were not imported')
                if response['data']['transaction_ids']:
                    print(f'Account {bank_config.iban}: {len(response["data"]["transaction_ids"])} transactions imported to YNAB')
    else:
        print('Connection to YNAB API failed')
