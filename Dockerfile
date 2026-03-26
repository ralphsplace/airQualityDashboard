# Stage 1: Build the frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first for better layer caching
COPY package*.json ./
# If you use npm ci, package-lock.json should exist
RUN npm ci

# Copy the rest of the app
COPY . .

ARG VITE_API_BASE_URL=http://localhost:8008
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the production bundle
RUN npm run build


# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy built frontend assets to serve them with the backend
RUN mkdir -p /dist
COPY --from=builder /app/dist /dist

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8008

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
