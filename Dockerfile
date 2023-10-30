FROM python:3.10
WORKDIR /authentication
COPY . .
CMD ["flask","run","--host","0.0.0.0"]
