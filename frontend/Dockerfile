FROM node:22-alpine
WORKDIR /app/frontend
COPY package*.json /app/frontend/
RUN npm install
COPY . /app/frontend
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]