# ADR-0022 - Subsistema de referência como fronteira normativa

## Status

Aceita em 2026-08-03.

## Contexto

Integrações reais combinavam contratos, processos, bancos, autenticação,
gateways e exposições diferentes. Falhas desses componentes contaminavam a
validação do núcleo e impediam distinguir defeito da plataforma de desvio do
subsistema.

## Decisão

O `sister_reference` é o único alvo operacional dos perfis oficiais de
validação. Ele implementa o contrato mínimo `sister.subsystem/1.0.0`, escuta
somente em `127.0.0.1:19001`, não possui persistência nem gateway e aceita
identidade funcional somente quando mediada pelo `sisterd` com token interno.

A API normativa usa `/manifest`, `/health`, `/ready`, `/capabilities`,
`/identity` e `/echo`. O descritor executável é
`contracts/subsystem/1.0.0/interface.json`; a referência canônica é
`reference/sister-reference`. Snapshots duplicados do executável não constituem
mais laboratório válido.

Integrações reais ficam em estado `quarantined`, com
`operational_access: false`. Elas não são iniciadas, roteadas, apresentadas no
catálogo vigente nem usadas como evidência de maturidade do núcleo. ADRs,
contratos e evidências anteriores permanecem históricos e não autorizam
reativação.

Perfis oficiais:

- `dev-core`: núcleo local, sem subsistema;
- `dev-reference`: núcleo local e referência obrigatória;
- `dev-lan`: gateway federador, núcleo por socket Unix e referência;
- `sec-03v`: segurança validada contra referência, nunca contra integração real.

Os aliases `dev-ecosystem` e `dev-ecosystem-strict` foram retirados após a
estabilização desta decisão. Evidências antigas que os mencionem permanecem
históricas e não definem perfis executáveis atuais.

## Reintegração

Subsistema real só sai da quarentena após evidenciar identidade contratual,
endpoint interno, health/readiness, startup e shutdown governáveis, ausência de
porta pública própria, mediação pelo SisTer, timeouts, falhas previsíveis, logs
observáveis e maturidade própria. Decisão exige nova ADR ou adendo explícito.

## Consequências

Validação fica reproduzível e parametrizável. Funcionalidade científica real
não participa desta fase. `PASS` prova plataforma e contrato de referência; não
certifica subsistema externo.
