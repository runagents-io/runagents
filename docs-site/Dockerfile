FROM public.ecr.aws/docker/library/python:3.12-alpine AS builder
WORKDIR /docs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ARG DOCS_VERSION=dev
ENV DOCS_VERSION=${DOCS_VERSION}
ARG GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
ENV GOOGLE_ANALYTICS_ID=${GOOGLE_ANALYTICS_ID}
RUN mkdocs build --strict

FROM public.ecr.aws/docker/library/nginx:alpine
COPY --from=builder /docs/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
