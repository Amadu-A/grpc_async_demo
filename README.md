# grpc_async_demo
grpc_async_demo

```commandline
grpc_async_demo/
├── proto/
│   └── calc.proto
├── server/
│   └── server_async.py
└── web/
    └── web_async.py

```
## Сгенерируйте Python-артефакты (один раз, при изменениях .proto — повторить):
```commandline
python -m pip install -U grpcio grpcio-tools
python -m grpc_tools.protoc \
  -I ./proto \
  --python_out=./server --grpc_python_out=./server \
  ./proto/calc.proto

# те же файлы нужны и веб-клиенту
cp server/calc_pb2.py server/calc_pb2_grpc.py web/

```

## Запуск:
```commandline
python server/server_async.py

```
## Запуск веб-клиента:
```commandline
python -m pip install -U fastapi uvicorn
python web/web_async.py
# откройте http://localhost:8000

```