# server/server_async.py
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable

import grpc
from grpc import aio

import calc_pb2
import calc_pb2_grpc


class CalculatorServicer(calc_pb2_grpc.CalculatorServicer):
    async def Add(
        self,
        request: calc_pb2.AddRequest,
        context: aio.ServicerContext,
    ) -> Awaitable[calc_pb2.AddReply]:
        # Никаких блокировок — чистая async-ветка
        a = int(request.a)
        b = int(request.b)
        return calc_pb2.AddReply(sum=a + b)


async def serve(address: str = "0.0.0.0:50051") -> None:
    server = aio.server(options=(("grpc.so_reuseport", 0),))
    calc_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    server.add_insecure_port(address)
    logging.info("Starting gRPC server on %s", address)
    await server.start()

    # Грациозная остановка
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        await server.stop(grace=None)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(serve())
