from collections.abc import Awaitable, Callable
from xml.etree import ElementTree as ET

from fastapi import FastAPI, HTTPException, Request, Response
from wechatpy.crypto import WeChatCrypto

from opencs.channel.schema import InboundMessage
from opencs.channel.wecom_cs import WecomCSConfig, WecomCustomerServiceAdapter

InboundHandler = Callable[[InboundMessage], Awaitable[None]]


def register_wecom_routes(
    app: FastAPI,
    adapter: WecomCustomerServiceAdapter,
    handler: InboundHandler,
) -> None:
    def _get_crypto() -> WeChatCrypto:
        config = adapter._config  # noqa: SLF001
        if not isinstance(config, WecomCSConfig):
            raise RuntimeError("WecomCustomerServiceAdapter must be installed before use")
        return WeChatCrypto(config.token, config.encoding_aes_key, config.corp_id)

    @app.get("/webhook/wecom_cs")
    async def verify(
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str,
    ) -> Response:
        crypto = _get_crypto()
        try:
            payload = crypto.verify_url(msg_signature, timestamp, nonce, echostr)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"verify failed: {e}") from e
        return Response(content=payload, media_type="text/plain")

    @app.post("/webhook/wecom_cs")
    async def callback(
        request: Request,
        msg_signature: str,
        timestamp: str,
        nonce: str,
    ) -> Response:
        crypto = _get_crypto()
        body = (await request.body()).decode()
        try:
            decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"decrypt failed: {e}") from e

        decrypted = _xml_to_flat_dict(decrypted_xml)
        msg = await adapter.parse_inbound({"decrypted": decrypted})
        await handler(msg)
        return Response(content="success", media_type="text/plain")


def _xml_to_flat_dict(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    return {child.tag: (child.text or "") for child in root}
