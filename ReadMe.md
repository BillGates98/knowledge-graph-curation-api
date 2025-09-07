# Knowledge Graph Curation API

This application allows you to calculate, detect and modify redundant information in the subject, predicate and object axes of a SPARQL endpoint.

## 💿 Install python 

| [python >= 3.8](https://www.python.org/downloads/) | [pip](https://pip.pypa.io/en/stable/installation/) |


After completing the installation, create the virtual environment and install the dependencies with pip.

```
python -m venv env .

python -m pip install -r requirements.txt

```

## ✨ Features

- ⚡  **Optimized Similarity computation**: The similarity computation process is based on LSH algorithm .
- 🧩  **Massive string similarity computation**: can reduce 100M of comparison to less than 1% of true similar strings.
- ⚡  **Unblocking processing**: Background processing with real-time progression diffusion.
- ⚡ **Fetch computed similarities**: You can directly search available similarities few moment after the starting of the massive computation.

These features are implemented in the backend side : [https://github.com/BillGates98/knowledge-graph-curation-api](https://github.com/BillGates98/knowledge-graph-curation-api) .

## 💡 Usage

This section covers how to start the server.

### Starting the DataBase Management System with docker (Recommended)

To start mysql server, run the following command.

```bash
docker run -d \
  --name kgc-mysql-db \
  --restart always \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=kgcuration \
  -e MYSQL_USER=admin \
  -e MYSQL_PASSWORD=root \
  -p 3306:3306 \
  -v db_data:/var/lib/mysql \
  mysql:8.4
```

### Starting the Backend Server (Recommended)

To start the development server with hot-reload, run the following command. 

```bash
./start-server.sh
```

### Start the Frontend Server

[https://github.com/BillGates98/knowledge-graph-curation](https://github.com/BillGates98/knowledge-graph-curation)


## 📑 License
[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2005-2025 Django Software Foundation and individual contributors. Django is a registered trademark of the Django Software Foundation.
