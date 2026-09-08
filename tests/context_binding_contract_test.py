#!/usr/bin/env python3

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "contracts/context-binding/1.0.0"
CONTEXT_REFERENCE = ROOT / "contracts/context-reference/1.0.0"

schema = json.loads(
    (CONTRACT / "context-binding.schema.json").read_text(encoding="utf-8")
)

example = json.loads(
    (CONTRACT / "examples/activity-unit-binding.json").read_text(
        encoding="utf-8"
    )
)

context_reference_schema = json.loads(
    (CONTEXT_REFERENCE / "context-reference.schema.json").read_text(
        encoding="utf-8"
    )
)

readme = (CONTRACT / "README.md").read_text(encoding="utf-8")


# Identidade do contrato.
assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
assert schema["properties"]["schema"]["const"] == \
    "sister.context-binding/1.0.0"
assert schema["additionalProperties"] is False

assert schema["required"] == [
    "schema",
    "binding_id",
    "relation",
    "subject",
    "object",
    "declared_by",
]


# O binding reutiliza a identidade federativa já definida pelo
# context-reference em vez de duplicá-la.
reference_ref = (
    "../../context-reference/1.0.0/"
    "context-reference.schema.json#/$defs/reference"
)

authority_ref = (
    "../../context-reference/1.0.0/"
    "context-reference.schema.json#/$defs/reference/properties/authority"
)

assert schema["properties"]["subject"]["$ref"] == reference_ref
assert schema["properties"]["object"]["$ref"] == reference_ref
assert schema["properties"]["declared_by"]["$ref"] == authority_ref


# O contrato deliberadamente não cria catálogo ou ontologia central
# de relações.
assert "enum" not in schema["properties"]["relation"]


# Registry contendo a fonte autoritativa da identidade federativa.
registry = Registry().with_resource(
    context_reference_schema["$id"],
    Resource.from_contents(context_reference_schema),
)

validator = Draft202012Validator(
    schema,
    registry=registry,
)

validator.check_schema(schema)
validator.validate(example)


# O exemplo central deve permanecer neutro em relação aos participantes.
serialized = json.dumps(
    example,
    ensure_ascii=False,
).lower()

for participant_name in (
    "nexo",
    "urt",
    "atmos",
    "praxis",
    "morfocampo",
):
    assert participant_name not in serialized


# Os extremos preservam exclusivamente a identidade federativa.
for endpoint in ("subject", "object"):
    assert set(example[endpoint]) == {
        "authority",
        "kind",
        "id",
    }


# declared_by é obrigatório.
without_declarer = copy.deepcopy(example)
del without_declarer["declared_by"]

try:
    validator.validate(without_declarer)
except ValidationError:
    pass
else:
    raise AssertionError(
        "binding sem declared_by deveria ser inválido"
    )


# Um endpoint sem autoridade é inválido.
without_authority = copy.deepcopy(example)
del without_authority["subject"]["authority"]

try:
    validator.validate(without_authority)
except ValidationError:
    pass
else:
    raise AssertionError(
        "subject sem authority deveria ser inválido"
    )


# Labels ou nomes não podem contaminar a identidade federativa.
with_label = copy.deepcopy(example)
with_label["object"]["label"] = "Bagé"

try:
    validator.validate(with_label)
except ValidationError:
    pass
else:
    raise AssertionError(
        "label não pode fazer parte da referência"
    )


# Proveniência e evidência são opcionais.
minimal = copy.deepcopy(example)
minimal.pop("provenance_ref")
minimal.pop("evidence_refs")

validator.validate(minimal)


# Guardas semânticas contra expansão indevida de escopo.
normalized_readme = " ".join(readme.split())

for statement in (
    "Nomes, títulos, labels e descrições NÃO estabelecem vínculo.",
    "A relação é declarada, não inferida pelo SisTer.",
    "NÃO constitui prova de identidade nem de relação.",
    "O binding não transfere autoridade de domínio ao SisTer.",
    "`sister.relation/1.0.0` NÃO é reutilizado para este propósito.",
    "Nada além disso pertence ao `WEB-CONTENT-02B0-B`.",
):
    assert statement in normalized_readme


print("context binding contract test: ok")
