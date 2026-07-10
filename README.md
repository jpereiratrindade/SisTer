# SisTer

SisTer e um teste de plataforma federativa de convergencia territorial orientada por contratos.

```text
SisTer nao integra sistemas porque controla seus codigos.
SisTer integra sistemas porque reconhece contratos comuns.
```

## Hipotese

O centro do projeto e `contracts/`, nao `apps/`. Sistemas como MorfoCampo, DroneOps, CampoNode e Radar podem manter autonomia operacional, interface propria e sincronizacao offline, desde que entreguem contratos comuns, evidencias e proveniencia verificavel.

## Base tecnica

- C++20 como padrao inicial.
- CMake para build.
- `sister_core` como biblioteca de dominio.
- `sisterctl` como CLI minima para validar manifestos.
- `web/` como primeira interface estatica de convergencia e inspecao.
- Contratos JSON Schema em `contracts/`.
- Governanca inspirada na estrutura usada em `LabGestao/docs`.

C++20 e uma escolha conservadora e portavel. C++23 pode ser adotado depois em modulos isolados se houver ganho real com `std::expected`, ranges mais completos ou melhorias de biblioteca aceitas pelo toolchain alvo.

## Build

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Validar um manifesto

```bash
./build/apps/sisterctl/sisterctl validate-manifest examples/morfocampo_manifest_example.json
```

## Interface

A primeira interface nao depende de servidor. Abra:

```text
web/index.html
```

Ela apresenta uma visao operacional dos sistemas federados, contratos de integracao, evidencias, proveniencia e um mapa territorial sintetico para validar o conceito de convergencia.

## Qualidade e governanca

```bash
python3 scripts/validate_governance_repo.py
python3 scripts/validate_tool_contracts.py
./scripts/run_quality.sh
```
