FROM python:3.12-alpine
WORKDIR /app
COPY server.py index.html ./
RUN mkdir -p /app/data
EXPOSE 8080
CMD ["python","-u","server.py"]
