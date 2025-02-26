# How to run

## Requirements

- Python 3.12 (other versions will not work)
- Node.js 23 (other versions may work)

## Install dependencies

```bash
pip install -r requirements.txt
```

```bash
prisma migrate dev --name init
```

```bash
cd home_security
npm i
npm run build
```

Go to the root directory of the project and run the following commands (you need three terminals open):

## Run the Camera

```bash
python cam.py
```

## Run the server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Run the client

```bash
cd home_security
npm start
```
