import re
from contextvars import ContextVar, Token
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
_MISSING_REQUEST_ID = "-"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

_request_ctx: ContextVar[Request | None] = ContextVar("request", default=None)


def get_request() -> Request | None:
    """
    Get the request from the request context.
    """
    return _request_ctx.get()


def get_request_id() -> str:
    """
    Get the request ID from the request context.
    """
    request = get_request()
    if request is None:
        return _MISSING_REQUEST_ID
    request_id = getattr(request.state, "request_id", None)
    if not request_id or not isinstance(request_id, str):
        return _MISSING_REQUEST_ID
    return request_id


class RequestContextMiddleware:
    """
    Bind the current HTTP request for the lifetime of one ASGI call.

    Stores a Starlette Request wrapping the live scope, assigns X-Request-ID,
    and resets the ContextVar when the request completes.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        request_id = self.__resolve_request_id(headers.get(REQUEST_ID_HEADER))
        headers[REQUEST_ID_HEADER] = request_id

        request = Request(scope, receive)
        request.state.request_id = request_id
        context_token: Token[Request | None] = _request_ctx.set(request)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(raw=message.setdefault("headers", []))
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _request_ctx.reset(context_token)

    def __resolve_request_id(self, header_value: str | None) -> str:
        """
        Resolve the request ID from the header value.
        """
        if header_value is None:
            return str(uuid4())
        candidate = header_value.strip()
        if _REQUEST_ID_PATTERN.fullmatch(candidate):
            return candidate
        return str(uuid4())
