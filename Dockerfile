FROM python:3-alpine

WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python3", "fints_to_ynab.py" ]
