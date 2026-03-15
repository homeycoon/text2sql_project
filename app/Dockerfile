FROM python:3.10-slim

RUN mkdir app
WORKDIR app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
CMD python create_fake_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload