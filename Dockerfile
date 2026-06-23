FROM python:3.12-slim

WORKDIR /app 
COPY pyproject.toml .
COPY focus/ focus/ 

RUN pip install -e ".[dev]"

ENTRYPOINT ["focus"]
CMD ["--help"]
