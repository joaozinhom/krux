# The MIT License (MIT)

# Copyright (c) 2021-2026 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Single point of entry for SHA-256 hashing.

Krux uses SHA-256 in two semantically different ways, and mixing them up is a
real hazard:

- `sha256()` is a plain, single SHA-256. Anything hashed with it can be
  reproduced by the user outside of Krux, with `sha256sum` or any other tool.
  Every hash Krux *shows on screen* for verification must be this one.

- `sha256d()` is a double SHA-256, `SHA256(SHA256(x))`. This is a Bitcoin
  protocol internal (BIP-137 message preimages, base58check, txids). It is
  NOT what a user gets by hashing the same input by hand, so it must never be
  presented as "the SHA256 of" something.

Both route through `uhashlib_hw`, the K210 hardware-accelerated implementation,
falling back to `hashlib` off-device. Import from here rather than reaching for
`hashlib` or `uhashlib_hw` directly, so the choice of backend stays in one
place.
"""

try:
    import uhashlib_hw as _backend

    _pbkdf2 = _backend.pbkdf2_hmac_sha256
except ImportError:  # off-device (tooling, docs); no hardware acceleration
    import hashlib as _backend

    def _pbkdf2(secret, salt, iterations):
        return _backend.pbkdf2_hmac("sha256", secret, salt, iterations)


def sha256(data=b""):
    """
    Single SHA-256 hasher, as `hashlib.sha256`.

    Returns a hasher object, so it accepts `.update()` for streaming and
    `.digest()` for the result. Use this for any hash the user is expected to
    reproduce or verify externally.
    """
    return _backend.sha256(data)


def sha256d(data):
    """
    Double SHA-256 digest, `SHA256(SHA256(data))`, as used by Bitcoin.

    Returns the digest bytes directly, since there is no meaningful streaming
    use for it. Never display this as "SHA256" -- it will not match what the
    user computes by hand.
    """
    return _backend.sha256(_backend.sha256(data).digest()).digest()


def pbkdf2_hmac_sha256(secret, salt, iterations):
    """PBKDF2-HMAC-SHA256 key stretching"""
    return _pbkdf2(secret, salt, iterations)
