from __future__ import annotations

import logging
import subprocess
import time

from finops_api.providers.common.types import CanonicalCostRow

__all__ = ["CanonicalCostRow", "run_cli_with_retry"]

logger = logging.getLogger(__name__)


def run_cli_with_retry(
    command: list[str],
    *,
    timeout: int = 300,
    max_attempts: int = 3,
    retry_delay: float = 5.0,
    env: dict[str, str] | None = None,
    label: str = "CLI",
) -> str:
    last_error: str | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            if result.returncode == 0:
                return result.stdout
            last_error = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        except subprocess.TimeoutExpired:
            last_error = f"Timeout apos {timeout}s"
        except FileNotFoundError as exc:
            executable = command[0] if command else "comando"
            raise RuntimeError(f"{label} indisponivel: binario '{executable}' nao encontrado no ambiente") from exc

        if attempt < max_attempts:
            backoff = retry_delay * attempt
            logger.warning(
                "%s tentativa %d/%d falhou (%s). Retry em %.1fs...",
                label, attempt, max_attempts, last_error, backoff,
            )
            time.sleep(backoff)

    raise RuntimeError(f"Falha no {label} apos {max_attempts} tentativas: {last_error}")
