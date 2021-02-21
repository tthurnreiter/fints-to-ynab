from fints.client import FinTS3PinTanClient
from fints.utils import minimal_interactive_cli_bootstrap
from datetime import date, timedelta
from models import Transaction
import hashlib

def transform_paypal_transaction(payee, memo):
    if 'paypal' in payee.lower():
        if 'Ihr Einkauf' in memo:
            payee = memo[memo.find('Ihr Einkauf bei ') + 16 : None if memo.find('AWV-MELDEPFLICHT') == -1 else memo.find('AWV-MELDEPFLICHT')]
            memo = 'PayPal'
        else:
            memo = 'PayPal'
    return payee, memo

def is_cash_withdrawl(transaction):
    if transaction['posting_text'] and "BARGELD" in transaction['posting_text']:
        return True
    return False

def transform_fints_transaction(transaction, parse_paypal=False):
    payee = transaction['applicant_name'] or ''
    memo = transaction['purpose'] or ''

    if parse_paypal:
        payee, memo = transform_paypal_transaction(payee, memo)

    memo = f"{transaction['posting_text'] or ''} / {memo}"

    return Transaction(
        date=transaction['date'].isoformat(),
        amount=int(transaction['amount'].amount * 1000),
        payee=payee,
        memo=memo,
        cash_withdrawl = is_cash_withdrawl(transaction),
        hash = hashlib.sha256( ("%s:%s:%s:%s"%(transaction['applicant_name'], transaction['purpose'], transaction['amount'].amount,  transaction['date'].isoformat() )).encode('utf-8') ).hexdigest()
    )

def get_transactions(bank_config):
    f = FinTS3PinTanClient(
        bank_config.blz,
        bank_config.login,
        bank_config.pin,
        bank_config.fints_endpoint,
        product_id='33D93BB1B017D422A87837C01'
    )

#    minimal_interactive_cli_bootstrap(f)
#
#    with f:
#        # Since PSD2, a TAN might be needed for dialog initialization. Let's check if there is one required
#        if f.init_tan_response:
#            print("A TAN is required", f.init_tan_response.challenge)
#            tan = input('Please enter TAN:')
#            f.send_tan(f.init_tan_response, tan)
#        # Fetch accounts
    accounts = f.get_sepa_accounts()

    # get transactions
    account = next(filter(lambda a: a.iban == bank_config.iban, accounts), None)
    transactions = f.get_transactions(account, date.today()-timedelta(days=10))

    return list(map(lambda t: transform_fints_transaction(t.data, parse_paypal=bank_config.parse_paypal), transactions))
