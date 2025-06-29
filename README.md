#### Init venv
`source .venv/bin/activate`

#### Install packages
`uv sync`

#### Start db
`docker compose up`

#### Start Server
`uv run main.py`

#### Login to db
`psql -U postgres -h localhost -d langchain_company`

#### list tables
`\dt`

