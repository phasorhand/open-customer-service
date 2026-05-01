import time

import pytest

from opencs.harness.token import HarnessToken, InvalidTokenError, TokenFactory


def _factory(ttl: int = 60) -> TokenFactory:
    return TokenFactory(secret_key=b"test-secret", default_ttl_seconds=ttl)


def test_token_verifies_correct_action_id() -> None:
    tf = _factory()
    tok = tf.issue(action_id="act-1", args={"tool": "crm_read", "customer_id": "c1"})
    tok.verify(action_id="act-1")  # must not raise


def test_token_rejects_wrong_action_id() -> None:
    tf = _factory()
    tok = tf.issue(action_id="act-1", args={})
    with pytest.raises(InvalidTokenError, match="action_id"):
        tok.verify(action_id="act-2")


def test_token_rejects_expired() -> None:
    tf = _factory(ttl=0)
    tok = tf.issue(action_id="act-1", args={})
    time.sleep(0.01)
    with pytest.raises(InvalidTokenError, match="expired"):
        tok.verify(action_id="act-1")


def test_token_rejects_tampered_signature() -> None:
    tf = _factory()
    tok = tf.issue(action_id="act-1", args={})
    tampered = HarnessToken(
        action_id=tok.action_id,
        args_hash=tok.args_hash,
        expires_at=tok.expires_at,
        signature=b"bad" + tok.signature[3:],
    )
    with pytest.raises(InvalidTokenError, match="mismatch"):
        tf.verify(tampered, action_id="act-1")


def test_token_rejects_verify_with_no_key_available() -> None:
    tf = _factory()
    tok = tf.issue(action_id="act-1", args={})
    keyless = HarnessToken(
        action_id=tok.action_id,
        args_hash=tok.args_hash,
        expires_at=tok.expires_at,
        signature=tok.signature,
    )
    with pytest.raises(InvalidTokenError, match="no secret key"):
        keyless.verify(action_id="act-1")


def test_different_factories_with_different_secrets_reject_each_others_tokens() -> None:
    tf1 = TokenFactory(secret_key=b"secret-A", default_ttl_seconds=60)
    tok = tf1.issue(action_id="act-1", args={})
    # Manually verify using a different secret should fail
    with pytest.raises(InvalidTokenError, match="signature"):
        HarnessToken(
            action_id=tok.action_id,
            args_hash=tok.args_hash,
            expires_at=tok.expires_at,
            signature=tok.signature,
        ).verify(action_id="act-1", secret_key=b"secret-B")


def test_token_satisfies_execution_token_protocol() -> None:
    from opencs.channel.exec_token import ExecutionToken

    tf = _factory()
    tok = tf.issue(action_id="act-1", args={})
    assert isinstance(tok, ExecutionToken)
