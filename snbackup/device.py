import httpx


class Device:
    """Manages httpx Client."""

    def __init__(self, base_url: str, timeout=1) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def http_request(self, uri: str, document=None) -> httpx.Response:
        """Downloads and uploads files to remote device."""
        if document:
            response = self.client.post(uri, files=document)
        else:
            response = self.client.get(uri)
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.client.close()

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.base_url}, {self.timeout})'
