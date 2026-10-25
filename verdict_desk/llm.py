"""Cliente de LLM com modo offline para testes. Dois formatos, so biblioteca padrao:

- padrao: API de chat no formato da OpenAI (Mistral, ou qualquer outra via MISTRAL_BASE_URL e MISTRAL_MODEL);
- LLM_PROVIDER=anthropic: Claude pela API de Mensagens nativa (modelo padrao claude-haiku-5-5).

A chave vem so da variavel de ambiente MISTRAL_API_KEY. Sem chave, `available()`
e falso e os agentes LLM nao rodam (o nucleo deterministico segue sozinho).

O plano gratuito da Mistral aceita poucas requisicoes por segundo: o cliente espaca
o inicio das chamadas (tambem entre threads, como nos lotes paralelos da narrativa) e
tenta de novo em 429 e 5xx. Nenhuma excecao deste modulo carrega a chave.
"""

import datetime
import email.utils
import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.request


def _number(name: str, default, cast, valid):
    """Le um numero do ambiente; vazio, ilegivel ou fora do intervalo valido volta ao padrao."""
    try:
        value = cast(os.environ.get(name) or default)
    except ValueError:
        return default
    return value if valid(value) else default


# LLM_PROVIDER=anthropic talks to Claude through the native Messages API; anything else is an OpenAI-style
# chat API (Mistral by default). The MISTRAL_* names are historical and still win over the provider defaults.
ANTHROPIC = os.environ.get("LLM_PROVIDER", "").strip().lower() == "anthropic"
BASE_URL = os.environ.get("MISTRAL_BASE_URL") or ("https://api.anthropic.com/v1" if ANTHROPIC else "https://api.mistral.ai/v1")
MODEL = os.environ.get("MISTRAL_MODEL") or ("claude-haiku-5-5" if ANTHROPIC else "mistral-small-latest")
ANTHROPIC_VERSION = "2023-06-01"
MAX_TOKENS = _number("MISTRAL_MAX_TOKENS", 3000, int, lambda v: v > 0)  # modelos com raciocinio gastam tokens antes da resposta
MIN_INTERVAL = _number("MISTRAL_MIN_INTERVAL", 1.1, float, lambda v: math.isfinite(v) and v >= 0)  # segundos entre inicios de chamada
MAX_RETRIES = 4
RETRY_STATUS = {429, 500, 502, 503, 504, 529}  # 529: the Anthropic API is overloaded
MAX_WAIT = 60.0

_gate = threading.Lock()
_next_start = 0.0


class LLMError(OSError):
    """Falha da chamada ao LLM. Herda de OSError para cair nos `except OSError` que ja existem."""


def _pause(seconds: float) -> None:
    time.sleep(seconds)


def _key() -> str:
    return os.environ.get("MISTRAL_API_KEY", "").strip()


def _anthropic() -> bool:
    return os.environ.get("LLM_PROVIDER", "").strip().lower() == "anthropic"


def _keyless() -> bool:
    """LLM_KEYLESS=1: the provider needs no key (a free anonymous tier).

    In this mode no Authorization header is sent at all, even when MISTRAL_API_KEY holds a key for
    another provider: a credential is never handed to a host it does not belong to.
    """
    return os.environ.get("LLM_KEYLESS", "").strip() == "1"


def available() -> bool:
    return bool(_key()) or _keyless()


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


def _retry_delay(err: urllib.error.HTTPError, attempt: int) -> float | None:
    """Segundos ate a proxima tentativa, ou None quando o servidor pede mais que MAX_WAIT.

    `Retry-After` vale em segundos ou como data HTTP. Tentar antes do pedido so gastaria
    tentativas contra o mesmo limite, e esperar mais que MAX_WAIT seguraria a rodada horaria:
    nesse caso o erro e registrado na hora. Sem cabecalho utilizavel, recuo exponencial.
    """
    value = (err.headers or {}).get("Retry-After")
    wait = None
    if value is not None:
        try:
            wait = float(value)
        except (TypeError, ValueError):
            try:
                wait = (email.utils.parsedate_to_datetime(value) - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            except (TypeError, ValueError):
                wait = None
    if wait is None or math.isnan(wait):
        return min(2.0 ** (attempt + 1), MAX_WAIT)
    wait = max(0.0, wait)
    return wait if wait <= MAX_WAIT else None


def _read_detail(err: urllib.error.HTTPError) -> str:
    try:
        detail = err.read(600).decode("utf-8", "replace")
        err.close()
        return detail
    except Exception:  # corpo ausente ou ja consumido: o status basta
        return ""


def _free_limit_delay(err: urllib.error.HTTPError, detail: str) -> float | None:
    """A free anonymous tier answers HTTP 402 FREE_LIMIT with "Retry after Ns": wait that long, once it fits MAX_WAIT."""
    if err.code != 402 or "FREE_LIMIT" not in detail:
        return None
    found = re.search(r"[Rr]etry after (\d+)\s*s", detail)
    wait = float(found.group(1)) + 1.0 if found else 31.0
    return wait if wait <= MAX_WAIT else None


def _http_error(err: urllib.error.HTTPError, key: str, detail: str | None = None) -> LLMError:
    # O erro vai para o dossie: inclui o corpo da resposta (curto, sem a chave) para a causa aparecer no historico.
    if detail is None:
        detail = _read_detail(err)
    if key:  # an empty key would be "redacted" into every gap of the text
        detail = detail.replace(key, "***")
    detail = detail[:300].replace("\n", " ").strip()
    return LLMError(f"HTTP {err.code} {err.reason} from {BASE_URL} model {MODEL}: {detail or 'no body'}")


def _first_choice(raw: bytes) -> dict:
    try:
        choice = json.loads(raw.decode("utf-8"))["choices"][0]
    except (KeyError, IndexError, TypeError):
        choice = None
    if not isinstance(choice, dict):
        raise ValueError("unexpected response shape from the Mistral API")
    return choice


def _anthropic_text(raw: bytes) -> str:
    """The answer of a Messages API response: its text blocks, joined. Thinking blocks are not the answer."""
    try:
        data = json.loads(raw.decode("utf-8"))
        blocks = data["content"]
    except (KeyError, TypeError, ValueError):
        raise ValueError("unexpected response shape from the Anthropic API") from None
    text = "".join(str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("type") == "text")
    if text:
        return text
    stop = data.get("stop_reason")
    if stop == "refusal":
        category = (data.get("stop_details") or {}).get("category")
        raise ValueError(f"the model refused this request (stop_reason=refusal, category={category})")
    raise ValueError(f"model returned no text (stop_reason={stop}); raise MISTRAL_MAX_TOKENS" if stop == "max_tokens" else f"model returned no text (stop_reason={stop})")


def chat(system: str, user: str, timeout: int = 90, max_tokens: int | None = None) -> str:
    keyless = _keyless()
    key = "" if keyless else _key()
    if not keyless:
        if not key:
            raise LLMError("MISTRAL_API_KEY is not set")
        if not key.isprintable() or " " in key:
            # Nao ecoa o valor: um cabecalho invalido faz o urllib imprimir a chave no erro.
            raise LLMError("MISTRAL_API_KEY has spaces or control characters; paste only the key")
    native = _anthropic()
    if native:
        # Claude Haiku 5.5 rejects non-default sampling values with a 400, so no temperature; thinking is off so no
        # token is spent before the answer. The replay never calls the model: the text is frozen in the dossier.
        payload = {"model": MODEL, "max_tokens": max_tokens or MAX_TOKENS, "thinking": {"type": "disabled"},
                   "system": system, "messages": [{"role": "user", "content": user}]}
        url = f"{BASE_URL}/messages"
        headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION, "Content-Type": "application/json"}
    else:
        payload = {"model": MODEL, "temperature": 0, "max_tokens": max_tokens or MAX_TOKENS,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        url = f"{BASE_URL}/chat/completions"
        headers = {**({"Authorization": f"Bearer {key}"} if key else {}), "Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RETRIES + 1):
        _wait_turn()
        request = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
            if native:
                return _anthropic_text(raw)
            choice = _first_choice(raw)
            break
        except urllib.error.HTTPError as err:
            detail = _read_detail(err)
            delay = _retry_delay(err, attempt) if err.code in RETRY_STATUS and attempt < MAX_RETRIES else None
            if delay is None and keyless and attempt < MAX_RETRIES:
                delay = _free_limit_delay(err, detail)
            if delay is None:
                raise _http_error(err, key, detail) from err
            _pause(delay)
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
        "Be honest, but go through every item before giving up on your side: return an empty list only if no item can honestly be read in favor of it. "
        'Reply ONLY with a JSON list of objects {"claim": str, "cites": [evidence ids]}. '
        "Every evidence item starts with its id (E1, E2, ...) before the colon. You MUST cite items by those ids, "
        'written as strings exactly as listed: a claim that rests on items E3 and E14 has "cites": ["E3", "E14"]. '
        "A bare number such as 14 is not an id: a claim that does not cite by id is discarded. "
        "Write the ids only in cites, never inside the claim text. "
        "Rules: cite at least one evidence id per claim; every number in a claim must appear "
        "character-for-character in the cited evidence items — copy the exact string from the "
        "evidence item, NEVER round or reformat. If the evidence says '3.1596' you must write '3.1596', "
        "NOT '3.16'. If it says '4.53e-05' you must write '4.53e-05', NOT '0.00453%'. If it says "
        "'-19.79%' you must write '-19.79%', NOT '-19.8%'. Scientific notation, sign, decimal places, "
        "trailing zeros — all must be copied verbatim. A claim with a rounded or reformatted number "
        "will be DISCARDED by the validator. "
        "Examples — ACCEPTED claim: {\"claim\": \"Volume spiked to 125.3% of the 24h average, confirming breakout\", \"cites\": [\"E3\"]} (where E3 says 'volume ratio: 125.3%'). "
        "Examples — ACCEPTED claim with two items: {\"claim\": \"Bullish setup\", \"cites\": [\"E3\", \"E14\"]} (E3 and E14 both support it). "
        "Examples — REJECTED claim: {\"claim\": \"Volume spiked to 125% of average\", \"cites\": [\"E3\"]} (125 != 125.3, rounded). "
        "Examples — REJECTED claim: {\"claim\": \"Funding is slightly positive at 0.005%\", \"cites\": [\"E7\"]} (0.005 != 4.53e-05, reformatted). "
        "NEVER invent horizons, thresholds or percentages; "
        "at most 4 claims; the two sides pick different facts because each side favors different ones."
    )
    user = "\n".join(f"{k}: {v}" for k, v in evidence_items.items())
    return parse_claims(ask(system, user))
