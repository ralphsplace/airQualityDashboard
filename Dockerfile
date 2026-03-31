# Stage 1: Build the frontend
# FROM node:20-alpine AS builder

# WORKDIR /

# # Copy the rest of the app
# COPY . .

# ARG VITE_API_BASE_URL=http://localhost:8008
# ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# # Build the production bundle
# RUN npm install
# RUN npm run build

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
RUN pip install .

COPY app ./app
# COPY --from=builder dist ./dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
