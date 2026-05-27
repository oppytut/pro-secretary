FROM python:3.11-slim@sha256:a5b427ace4900267d93db34138e512325c6fa6af84ad5e4ed5f3b36258cc4142

ENV TZ=Asia/Jakarta

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends openssh-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

CMD ["sh", "-c", "mkdir -p /root/.ssh && cp /tmp/ssh_key /root/.ssh/id_ed25519 2>/dev/null; chmod 600 /root/.ssh/id_ed25519 2>/dev/null; exec python bot.py"]
