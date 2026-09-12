# Multi-stage build: build the Vite app, then serve the static output.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "serve -s dist -l ${PORT:-8080}"]
