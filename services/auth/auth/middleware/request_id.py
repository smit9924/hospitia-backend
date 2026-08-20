from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware:
    """
    ASGI middleware that assigns a UUID to every incoming HTTP request.

    The identifier is stored on the request headers and on the response as
    `X-Request-ID`. Read it from the Starlette `Request` in path operations
    and handlers via `request.headers.get(REQUEST_ID_HEADER)`.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())

        headers = MutableHeaders(scope=scope)
        headers[REQUEST_ID_HEADER] = request_id

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(raw=message.setdefault("headers", []))
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        await self.app(scope, receive, send_wrapper)
