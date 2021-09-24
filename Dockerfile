FROM python:3

WORKDIR /usr/src/app

# Install requirements
RUN apt update -y
RUN apt install -y \
	emacs \
	curl

ENV NODE_VERSION=14
ENV NVM_DIR=/root/.nvm
RUN mkdir ${NVM_DIR}
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version

COPY app .
RUN pip install --no-cache-dir -r requirements.txt

