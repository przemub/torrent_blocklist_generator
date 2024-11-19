FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install --root-user-action ignore -r requirements.txt

COPY blocklist.py .

USER nobody

ENTRYPOINT ["python", "blocklist.py"]

