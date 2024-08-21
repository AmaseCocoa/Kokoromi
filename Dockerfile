FROM python:3.12-slim

WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /usr/src/app
RUN cp prisma/prod.prisma prisma/schema.prisma
RUN rm -f prisma/prod.prisma

RUN prisma generate

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]