# Base conceitual viva do SisTer

O desenvolvimento conceitual do SisTer e mantido como base viva em:

```text
/run/media/jpereiratrindade/labeco10T/dev/Text/SisTer/
```

Neste repositorio, essa base deve ser acessada por:

```text
docs/conceptual -> ../../../Text/SisTer
```

## Decisao de integracao

A base conceitual nao deve ser copiada para dentro do repositorio tecnico como
material duplicado. Ela deve permanecer conectada, porque o proprio SisTer esta
sendo formulado como infraestrutura sociotecnica federativa cuja resiliencia
depende de coerencia durante reconfiguracao.

Copias documentais criariam risco de divergencia semantica: o codigo poderia
evoluir sobre uma versao congelada enquanto a ontologia, os principios e a
governanca seguiriam outro caminho. O link vivo preserva a relacao entre:

- construcao ontologica;
- principios de engenharia e governanca;
- DDD e ADRs candidatos;
- contratos, exemplos, validadores e implementacao C++.

## Regra de trabalho

Mudancas relevantes em contratos, DDD, DAI, ADRs, exemplos ou validadores devem
verificar a base conceitual conectada antes de serem tratadas como coerentes com
a direcao do SisTer.

Mudancas relevantes na base conceitual devem indicar, quando aplicavel, impacto
esperado sobre:

- `contracts/`;
- `core/`;
- `apps/sisterctl`;
- `apps/sisterd`;
- `web/`;
- `docs/architecture/`;
- `docs/governance/`;
- `docs/adr/`.

## Limite

O link vivo nao transforma documentos propostos em decisoes aceitas. Estados como
`Proposto`, `Aceito`, `Substituido` ou `Rejeitado` continuam sendo governados por
ADR, DAI e pelos documentos de governanca correspondentes.
