FROM python:3.12-slim

WORKDIR /app

# TODO: populate once demo project has real source
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "-m", "src"]
