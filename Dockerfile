FROM nikolaik/python-nodejs:latest
WORKDIR /usr/src/app

# Install requirements
RUN apt update -y
RUN apt install -y \
	emacs \
	vim 
COPY app .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app/page
RUN npm install
RUN ./node_modules/.bin/rollup -c rollup.config.js && \
	cp node_modules/vue/dist/vue.min.js dist/static/js/ && \
	cp node_modules/vue-router/dist/vue-router.min.js dist/static/js/ && \
	cp node_modules/vuex/dist/vuex.min.js dist/static/js && \
	cp node_modules/codemirror/lib/codemirror.js dist/static/js && \
	cp node_modules/graphology/dist/graphology.umd.js dist/static/js && \
	cp node_modules/graphology-layout-forceatlas2/build/graphology-layout-forceatlas2.min.js dist/static/js && \
	cp node_modules/sigma/build/sigma.min.js dist/static/js
RUN npm update -g npm

WORKDIR /usr/src/app
RUN chmod +x category.py

