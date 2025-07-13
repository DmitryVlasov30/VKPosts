FROM python:3.13.0
WORKDIR /bot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "src/main.py"]