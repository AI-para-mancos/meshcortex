import requests


def call_backend(prompt, base_url="http://localhost:8080/v1"):
    r = requests.post(
        f"{base_url}/chat/completions",
        json={
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
    )
    return r.json()["choices"][0]["message"]["content"]


print(call_backend("Explica que es un orquestador de LLMs en una frase"))
