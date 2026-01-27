import httpx


class Device:
    """Manages httpx Client."""

    def __init__(self, base_url: str, timeout: int = 1) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        self.memory = None
        self.mem_used = None

    def http_request(self, uri: str, document: dict = None) -> httpx.Response:
        """Downloads and uploads files to remote device."""
        if document:
            response = self.client.post(uri, files=document)
        else:
            response = self.client.get(uri)
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.client.close()

    def mem_usage(self) -> str | None:
        if self.memory and self.mem_used:
            return f'{self.mem_used / self.memory * 100:.2f}%'

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.base_url}, {self.timeout})'
