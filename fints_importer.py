from fints.client import FinTS3PinTanClient
from fints.utils import minimal_interactive_cli_bootstrap
from datetime import date, timedelta
from models import Transaction

def get_transactions(bank_config):
    f = FinTS3PinTanClient(
        bank_config['blz'],
        bank_config['login'],
        bank_config['pin'],
        bank_config['fints_endpoint'],
        product_id='33D93BB1B017D422A87837C01'
    )

    minimal_interactive_cli_bootstrap(f)

    with f:
        # Since PSD2, a TAN might be needed for dialog initialization. Let's check if there is one required
        if f.init_tan_response:
            print("A TAN is required", f.init_tan_response.challenge)
            tan = input('Please enter TAN:')
            f.send_tan(f.init_tan_response, tan)

        # Fetch accounts
        accounts = f.get_sepa_accounts()

    # get transactions
    account = next(filter(lambda a: a.iban == bank_config['iban'], accounts), None)
    transactions = f.get_transactions(account, date.today()-timedelta(days=10))

    def transform_fints_transaction(transaction):
        return Transaction(
            date=transaction['date'].isoformat(),
            amount=int(transaction['amount'].amount * 1000),
            payee=transaction['applicant_name'],
            memo=transaction['purpose'],
            cash_withdrawl= True if "BARGELD" in transaction['posting_text'] else False
        )

    return list(map(lambda t: transform_fints_transaction(t.data), transactions))
