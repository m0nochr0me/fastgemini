"""
SSL context creation and manipulation.
"""

import ctypes
import ctypes.util
import ssl
import sys
from pathlib import Path

# Load libssl for ctypes hack
_libssl_path = ctypes.util.find_library("ssl")
if not _libssl_path:
    _libssl_path = "libssl.so"  # Fallback
try:
    _libssl = ctypes.CDLL(_libssl_path)
    _libssl.SSL_CTX_set_verify.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
except Exception:
    _libssl = None


def _get_ssl_ctx_ptr(ssl_context: ssl.SSLContext) -> int | None:
    """Get SSL_CTX pointer from SSLContext - CPython implementation detail."""
    # The offset varies by Python version and platform
    # This is still fragile but at least documented
    if sys.implementation.name != "cpython":
        return None

    # For CPython 3.10+ on 64-bit Linux
    # struct PySSLContext has ctx at offset 16 (after PyObject_HEAD)
    try:
        return ctypes.cast(id(ssl_context) + 16, ctypes.POINTER(ctypes.c_void_p)).contents.value
    except Exception:
        return None


def _ignore_verify_errors(ssl_context: ssl.SSLContext) -> None:
    if not _libssl:
        return

    # Define callback that always returns 1 (success)
    ssl_verify_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p)

    def verify_cb(preverify_ok, x509_ctx):
        return 1

    # Keep reference to callback to prevent GC
    ssl_context._verify_cb = ssl_verify_cb(verify_cb)  # type: ignore

    ctx_ptr = _get_ssl_ctx_ptr(ssl_context)

    # SSL_VERIFY_PEER = 0x01
    _libssl.SSL_CTX_set_verify(ctx_ptr, 1, ssl_context._verify_cb)  # type: ignore


def create_server_ssl_context(
    certfile: Path,
    keyfile: Path,
) -> ssl.SSLContext:
    if not certfile or not keyfile:
        raise ValueError("Must set server certificate and key")

    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    sslcontext.check_hostname = False
    sslcontext.load_cert_chain(certfile, keyfile)
    sslcontext.verify_mode = ssl.CERT_OPTIONAL

    # Trust self-signed certificates by ignoring verification errors
    _ignore_verify_errors(sslcontext)

    return sslcontext
