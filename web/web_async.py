# web/web_async.py
from __future__ import annotations

import asyncio
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from grpc import aio

import calc_pb2
import calc_pb2_grpc

GRPC_TARGET = "localhost:50051"

app = FastAPI()
app.state.grpc_channel = None
app.state.grpc_stub = None


@app.on_event("startup")
async def on_startup() -> None:
    # Один долгоживущий асинхронный канал + stub — без создания на каждый запрос
    channel = aio.insecure_channel(GRPC_TARGET)
    # проверим соединение неблокирующим ping'ом
    await channel.channel_ready()
    stub = calc_pb2_grpc.CalculatorStub(channel)
    app.state.grpc_channel = channel
    app.state.grpc_stub = stub


@app.on_event("shutdown")
async def on_shutdown() -> None:
    channel: aio.Channel = app.state.grpc_channel
    if channel is not None:
        await channel.close()


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    # Простая страница: два input'а, кнопка и JS, который дергает /api/add
    return """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>gRPC async demo</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; }
    .box { max-width: 420px; display: grid; gap: 12px; }
    input { padding: 8px 10px; font-size: 1rem; }
    button { padding: 10px 12px; font-size: 1rem; cursor: pointer; }
    #result { font-weight: 600; }
  </style>
</head>
<body>
  <h1>Сложение через асинхронный gRPC</h1>
  <div class="box">
    <label>Первое число <input id="a" type="number" step="1" value="1"/></label>
    <label>Второе число <input id="b" type="number" step="1" value="2"/></label>
    <button id="calc">Рассчитать</button>
    <div>Сумма: <span id="result">—</span></div>
  </div>

  <script>
    const btn = document.getElementById('calc');
    const result = document.getElementById('result');

    btn.addEventListener('click', async () => {
      const a = parseInt(document.getElementById('a').value || '0', 10);
      const b = parseInt(document.getElementById('b').value || '0', 10);
      try {
        const resp = await fetch('/api/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ a, b })
        });
        if (!resp.ok) {
          const txt = await resp.text();
          throw new Error(txt || 'HTTP error');
        }
        const data = await resp.json();
        result.textContent = String(data.sum);
      } catch (e) {
        console.error(e);
        result.textContent = 'ошибка';
      }
    });
  </script>
</body>
</html>
    """


@app.post("/api/add", response_class=JSONResponse)
async def add(request: Request) -> JSONResponse:
    payload: Dict[str, Any] = await request.json()
    try:
        a = int(payload.get("a", 0))
        b = int(payload.get("b", 0))
    except (TypeError, ValueError):
        return JSONResponse({"error": "a and b must be integers"}, status_code=400)

    stub: calc_pb2_grpc.CalculatorStub = app.state.grpc_stub
    # Чисто асинхронный gRPC-вызов
    reply: calc_pb2.AddReply = await stub.Add(calc_pb2.AddRequest(a=a, b=b))
    return JSONResponse({"sum": int(reply.sum)})


if __name__ == "__main__":
    # uvicorn работает на asyncio и не блокирует event loop
    uvicorn.run("web_async:app", host="0.0.0.0", port=8000, reload=False)
