FROM nikolaik/python-nodejs:latest
WORKDIR /usr/src/app

# Install requirements
RUN apt update -y
RUN apt install -y \
	vim
COPY app .
RUN pip install --no-cache-dir -r requirements.txt

