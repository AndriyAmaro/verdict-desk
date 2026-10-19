"""Cliente Mistral (API de chat no formato da OpenAI) com modo offline para testes.

A chave vem so da variavel de ambiente MISTRAL_API_KEY. Sem chave, `available()`
e falso e os agentes LLM nao rodam (o nucleo deterministico segue sozinho).

O plano gratuito da Mistral aceita poucas requisicoes por segundo: o cliente espaca
o inicio das chamadas (tambem entre threads, como nos lotes paralelos da narrativa) e
tenta de novo em 429 e 5xx. Nenhuma excecao deste modulo carrega a chave.
"""

import json
import os
import threading
import time
import urllib.error
import urllib.request


def _number(name: str, default, cast):
    try:
        return cast(os.environ.get(name) or default)
    except ValueError:
        return default


BASE_URL = os.environ.get("MISTRAL_BASE_URL") or "https://api.mistral.ai/v1"
MODEL = os.environ.get("MISTRAL_MODEL") or "mistral-small-latest"
MAX_TOKENS = _number("MISTRAL_MAX_TOKENS", 3000, int)  # modelos com raciocinio gastam tokens antes da resposta
MIN_INTERVAL = _number("MISTRAL_MIN_INTERVAL", 1.1, float)  # segundos entre inicios de chamada
MAX_RETRIES = 4
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_WAIT = 60.0

_gate = threading.Lock()
_next_start = 0.0


class LLMError(OSError):
    """Falha da chamada ao LLM. Herda de OSError para cair nos `except OSError` que ja existem."""


def _pause(seconds: float) -> None:
    time.sleep(seconds)


def _key() -> str:
    return os.environ.get("MISTRAL_API_KEY", "").strip()


def available() -> bool:
    return bool(_key())


def message_text(content) -> str:
    """`content` vem como texto ou, em modelos com raciocinio, como lista de blocos; so o texto final conta."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


def _wait_turn() -> None:
    """Reserva o proximo horario de inicio de chamada; a reserva vale entre threads."""
    global _next_start
    with _gate:
        now = time.monotonic()
        start = max(now, _next_start)
        _next_start = start + MIN_INTERVAL
    if start > now:
        _pause(start - now)


def _retry_delay(err: urllib.error.HTTPError, attempt: int) -> float:
    try:
        return max(0.0, min(float((err.headers or {}).get("Retry-After")), MAX_WAIT))
    except (TypeError, ValueError):
        return min(2.0 ** (attempt + 1), MAX_WAIT)


def _http_error(err: urllib.error.HTTPError, key: str) -> LLMError:
    # O erro vai para o dossie: inclui o corpo da resposta (curto, sem a chave) para a causa aparecer no historico.
    detail = ""
    try:
        detail = err.read(300).decode("utf-8", "replace")
        err.close()
    except Exception:  # corpo ausente ou ja consumido: o status basta
        pass
    detail = detail.replace(key, "***").replace("\n", " ").strip()
    return LLMError(f"HTTP {err.code} {err.reason} from {BASE_URL} model {MODEL}: {detail or 'no body'}")


def _first_choice(raw: bytes) -> dict:
    try:
        choice = json.loads(raw.decode("utf-8"))["choices"][0]
    except (KeyError, IndexError, TypeError):
        choice = None
    if not isinstance(choice, dict):
        raise ValueError("unexpected response shape from the Mistral API")
    return choice


def chat(system: str, user: str, timeout: int = 90, max_tokens: int | None = None) -> str:
    key = _key()
    if not key:
        raise LLMError("MISTRAL_API_KEY is not set")
    if not key.isprintable() or " " in key:
        # Nao ecoa o valor: um cabecalho invalido faz o urllib imprimir a chave no erro.
        raise LLMError("MISTRAL_API_KEY has spaces or control characters; paste only the key")
    body = json.dumps(
        {"model": MODEL, "temperature": 0, "max_tokens": max_tokens or MAX_TOKENS, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    ).encode("utf-8")
    for attempt in range(MAX_RETRIES + 1):
        _wait_turn()
        request = urllib.request.Request(
            f"{BASE_URL}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                choice = _first_choice(response.read())
            break
        except urllib.error.HTTPError as err:
            if err.code not in RETRY_STATUS or attempt == MAX_RETRIES:
                raise _http_error(err, key) from err
            _pause(_retry_delay(err, attempt))
    message = choice.get("message")
    content = message_text(message.get("content") if isinstance(message, dict) else None)
    if not content:
        raise ValueError(f"model returned no content (finish_reason={choice.get('finish_reason')}); raise MISTRAL_MAX_TOKENS")
    return content


def parse_claims(text: str) -> list[dict]:
    """Extrai a lista JSON de afirmacoes da resposta; texto invalido vira lista vazia."""
    if not isinstance(text, str):
        return []
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except ValueError:
        return []
    return [c for c in data if isinstance(c, dict)]


STANCE = {
    "bull": "the strongest honest case for opening a LONG position now",
    "bear": "the strongest honest case against a long entry, or for a SHORT position",
}


def argue(side: str, evidence_items: dict[str, str], ask=chat) -> list[dict]:
    """Pede ao LLM argumentos de um lado, citando ids. `ask` permite injetar um stub."""
    system = (
        f"You are the {side} analyst in a market debate. Make {STANCE.get(side, 'your side of the case')}. "
        "Pick the evidence items that best support your side and say what each one implies for the next move. "
        "Be honest: if the evidence does not support your side, return fewer claims or an empty list. "
        'Reply ONLY with a JSON list of objects {"claim": str, "cites": [evidence ids]}. '
        "Rules: cite at least one evidence id per claim; every number in a claim must appear in a cited item, "
        "so never invent horizons, thresholds or percentages; at most 4 claims; "
        "the two sides pick different facts because each side favors different ones."
    )
    user = "\n".join(f"{k}: {v}" for k, v in evidence_items.items())
    return parse_claims(ask(system, user))
