FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates ffmpeg libsm6 libxext6\
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY install/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5000

# Start
CMD ["python", "main.py"]