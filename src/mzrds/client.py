from __future__ import annotations

import ssl
from typing import Any, Dict

from redis import Redis, from_url
from redis.cluster import RedisCluster

from .config import ConnectionOptions


def _build_ssl_kwargs(options: ConnectionOptions) -> Dict[str, Any]:
    if not options.tls and not any([options.cacert, options.cert, options.key]):
        return {}
    kwargs: Dict[str, Any] = {"ssl": True}
    cert_reqs = ssl.CERT_REQUIRED if options.cacert else ssl.CERT_NONE
    kwargs["ssl_cert_reqs"] = cert_reqs
    if options.cacert:
        kwargs["ssl_ca_certs"] = options.cacert
    if options.cert:
        kwargs["ssl_certfile"] = options.cert
    if options.key:
        kwargs["ssl_keyfile"] = options.key
    return kwargs


def _common_kwargs(options: ConnectionOptions) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "username": options.username,
        "password": options.password,
        "db": options.db,
        "decode_responses": False,
    }
    kwargs.update(_build_ssl_kwargs(options))
    return {k: v for k, v in kwargs.items() if v is not None}


def create_redis_client(options: ConnectionOptions) -> Redis:
    kwargs = _common_kwargs(options)
    if options.uri:
        return from_url(options.uri, **kwargs)
    return Redis(
        host=options.host,
        port=options.port,
        **kwargs,
    )


def create_cluster_client(options: ConnectionOptions) -> RedisCluster:
    kwargs = _common_kwargs(options)
    if options.uri:
        return RedisCluster.from_url(options.uri, **kwargs)
    return RedisCluster(
        host=options.host,
        port=options.port,
        **kwargs,
    )


def get_client(options: ConnectionOptions):
    if options.cluster:
        return create_cluster_client(options)
    return create_redis_client(options)


__all__ = [
    "get_client",
    "create_redis_client",
    "create_cluster_client",
]

