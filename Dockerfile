FROM python:3.12-alpine
WORKDIR /app
COPY server.py index.html event.html ./
COPY static ./static
RUN mkdir -p /app/data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3)" || exit 1
CMD ["python","-u","server.py"]
