import httpx
import base64
import time
from typing import Optional

# Language IDs for Judge0
LANGUAGE_IDS = {
    "python": 71,
    "python3": 71,
    "javascript": 63,
    "js": 63,
    "java": 62,
    "cpp": 54,
    "c++": 54,
    "c": 50,
    "typescript": 74,
    "go": 60,
    "rust": 73,
}

# Free public Judge0 instance
JUDGE0_URL = "https://judge0-ce.p.rapidapi.com"


class CodeRunner:
    """
    Runs code safely using Judge0 sandbox.
    Free tier available at judge0-ce.p.rapidapi.com
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            self.headers["X-RapidAPI-Key"] = api_key
            self.headers["X-RapidAPI-Host"] = "judge0-ce.p.rapidapi.com"

    def run(self, code: str, language: str, stdin: str = "") -> dict:
        """
        Execute code and return output.
        Returns dict with stdout, stderr, runtime_ms, success.
        """
        lang_id = LANGUAGE_IDS.get(language.lower())
        if not lang_id:
            return {
                "stdout": None,
                "stderr": f"Unsupported language: {language}. Supported: {', '.join(LANGUAGE_IDS.keys())}",
                "runtime_ms": None,
                "success": False,
            }

        # If no API key, use simple local execution for Python only
        if not self.api_key:
            return self._run_local(code, language)

        try:
            # Submit to Judge0
            encoded_code = base64.b64encode(code.encode()).decode()
            payload = {
                "source_code": encoded_code,
                "language_id": lang_id,
                "stdin": base64.b64encode(stdin.encode()).decode() if stdin else "",
                "encoding": "base64",
            }

            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=true",
                    json=payload,
                    headers=self.headers,
                )
                result = resp.json()

            stdout = base64.b64decode(result.get("stdout") or "").decode() if result.get("stdout") else None
            stderr = base64.b64decode(result.get("stderr") or "").decode() if result.get("stderr") else None
            runtime = int(float(result.get("time", 0) or 0) * 1000)

            return {
                "stdout": stdout,
                "stderr": stderr,
                "runtime_ms": runtime,
                "success": result.get("status", {}).get("id") == 3,  # 3 = Accepted
            }

        except Exception as e:
            return {
                "stdout": None,
                "stderr": str(e),
                "runtime_ms": None,
                "success": False,
            }

    def _run_local(self, code: str, language: str) -> dict:
        """
        Simple local execution for Python (dev only, no sandbox).
        Replace with Judge0 in production.
        """
        if language.lower() not in ("python", "python3"):
            return {
                "stdout": None,
                "stderr": "Local execution only supports Python. Add a Judge0 API key for other languages.",
                "runtime_ms": None,
                "success": False,
            }

        import subprocess
        import tempfile
        import os

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                fname = f.name

            start = time.time()
            result = subprocess.run(
                ["python", fname],
                capture_output=True,
                text=True,
                timeout=10,
            )
            runtime = int((time.time() - start) * 1000)
            os.unlink(fname)

            return {
                "stdout": result.stdout or None,
                "stderr": result.stderr or None,
                "runtime_ms": runtime,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": None,
                "stderr": "Time limit exceeded (10 seconds)",
                "runtime_ms": 10000,
                "success": False,
            }
        except Exception as e:
            return {
                "stdout": None,
                "stderr": str(e),
                "runtime_ms": None,
                "success": False,
            }


code_runner = CodeRunner()