#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/context-reference/1.0.0"

schema = json.loads(
    (CONTRACT / "context-reference.schema.json").read_text(encoding="utf-8")
)
example = json.loads(
    (CONTRACT / "examples/reference-set.json").read_text(encoding="utf-8")
)
readme = (CONTRACT / "README.md").read_text(encoding="utf-8")


# Identidade do contrato.
assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
assert schema["properties"]["schema"]["const"] == "sister.context-reference/1.0.0"
assert schema["additionalProperties"] is False
assert schema["required"] == ["schema", "refs"]


# A identidade federativa mínima é exatamente a tripla
# authority + kind + id.
reference = schema["$defs"]["reference"]
assert reference["required"] == ["authority", "kind", "id"]
assert reference["additionalProperties"] is False
assert set(reference["properties"]) == {"authority", "kind", "id"}


# O exemplo deve usar autoridades neutras: o contrato central não conhece
# participantes concretos para provar sua genericidade.
assert example["schema"] == "sister.context-reference/1.0.0"
assert example["refs"]

keys = set()
for ref in example["refs"]:
    assert set(ref) == {"authority", "kind", "id"}
    assert ref["authority"]
    assert ref["kind"]
    assert ref["id"]
    key = (ref["authority"], ref["kind"], ref["id"])
    assert key not in keys
    keys.add(key)

serialized = json.dumps(example, ensure_ascii=False).lower()
for participant_name in ("nexo", "urt", "atmos", "praxis", "morfocampo"):
    assert participant_name not in serialized


# Guardas semânticas mínimas do contrato.
# Normaliza apenas whitespace para que a validação semântica não dependa
# da quebra editorial de linhas no Markdown.
normalized_readme = " ".join(readme.split())

for statement in (
    "igualdade exige a igualdade da tripla",
    "nomes, títulos, labels e descrições NÃO constituem identidade federativa",
    "uma referência NÃO transfere autoridade de domínio ao SisTer",
    "NÃO são, por si só, prova de relação",
):
    assert statement in normalized_readme


# O primeiro contrato deliberadamente não inventa a relação que ainda
# não existe entre os participantes.
assert "vínculo entre referências" in readme
assert "projeto ativo" in readme
assert "intervalo temporal" in readme

print("context reference contract test: ok")
