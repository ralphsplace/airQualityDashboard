# Stage 1: Build the frontend
FROM node:20-alpine AS builder

WORKDIR /

# Copy the rest of the app
COPY . .

ARG VITE_API_BASE_URL=http://localhost:8008
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the production bundle
RUN npm install
RUN npm run build


# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GAIA_A08_URL=${GAIA_A08_URL}
ENV GAIA_A08_POLL_INTERVAL=${GAIA_A08_POLL_INTERVAL:-65}
ENV WAQI_ENABLED=${WAQI_ENABLED:-false}
ENV WAQI_TOKEN=${WAQI_TOKEN}  
ENV WAQI_URL=${WAQI_URL}
ENV WAQI_POLL_INTERVAL=${WAQI_POLL_INTERVAL:-300}

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY --from=builder dist ./dist
COPY public ./public
COPY config.yaml ./config.yaml

# Expose the port
EXPOSE 8008

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
