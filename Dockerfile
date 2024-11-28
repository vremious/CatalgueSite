FROM python:3.11-slim
ENV http_proxy http://10.248.36.11:3128
ENV https_proxy http://10.248.36.11:3128
RUN apt-get update -y && apt-get install mc -y libpq-dev gcc && pip install psycopg2 boto3
WORKDIR /app
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY . .
#RUN python manage.py makemigrations
RUN python manage.py collectstatic
#RUN python manage.py migrate

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

