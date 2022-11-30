FROM python:3.9.13
 
WORKDIR /app
 
ADD . /app
 
RUN pip install -r requirements.txt

EXPOSE 5000
CMD python __main__.py