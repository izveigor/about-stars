FROM python:3.8
WORKDIR /server
RUN pip install --upgrade pip
COPY requirements.txt /server/
RUN pip install -r requirements.txt
COPY . /server/