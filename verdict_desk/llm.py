"""Cliente NVIDIA NIM (compativel com OpenAI) com modo offline para testes.

A chave vem so da variavel de ambiente NVIDIA_API_KEY. Sem chave, `available()`
e falso e os agentes LLM nao rodam (o nucleo deterministico segue sozinho).
"""

import json
import os
import urllib.request

BASE_URL = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL = os.environ.get("NIM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
MAX_TOKENS = int(os.environ.get("NIM_MAX_TOKENS", "3000"))  # modelos de raciocinio gastam tokens antes da resposta


def available() -> bool:
    return bool(os.environ.get("NVIDIA_API_KEY"))


def chat(system: str, user: str, timeout: int = 90) -> str:
    body = json.dumps(
        {"model": MODEL, "temperature": 0, "max_tokens": MAX_TOKENS, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        choice = json.loads(response.read().decode("utf-8"))["choices"][0]
    content = choice["message"].get("content")
    if not content:
        raise ValueError(f"model returned no content (finish_reason={choice.get('finish_reason')}); raise NIM_MAX_TOKENS")
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
