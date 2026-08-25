# Compatibilidade: `sister.subsystem/1.0.0` → drafts ARC-01

> **Status: DRAFT / NOT RUNTIME-NORMATIVE**

Esta matriz documenta convivência e possíveis projeções. Ela não executa
migração, não autoriza integração e não altera a vigência de
`sister.subsystem/1.0.0`.

## Regra de coexistência

| Conjunto | Estado no ARC-01 | Consumidor operacional |
|---|---|---|
| `sister.subsystem/1.0.0` | normativo vigente e imutável | runtime e referência atuais |
| `sister.participant/2.0.0` | DRAFT / NOT RUNTIME-NORMATIVE | nenhum |
| `sister.capability-invocation/1.0.0` | DRAFT / NOT RUNTIME-NORMATIVE | nenhum |
| `sister.relation/1.0.0` | DRAFT / NOT RUNTIME-NORMATIVE | nenhum |

Não existe fallback, negociação automática ou preferência pelos drafts.

## Matriz de campos e conceitos

| `sister.subsystem/1.0.0` | Draft ARC-01 | Compatibilidade | Regra |
|---|---|---|---|
| `system_id` | `participant_id` e `identity.stable_id` | projetável com validação | os dois identificadores novos devem coincidir na declaração inicial |
| `name` | `name` | direta | limites de tamanho diferem e devem ser revalidados |
| versão do sistema | `version` do participante | direta | não confundir com versão dos contratos |
| ownership implícito/externo | `owner` | exige enriquecimento | owner deve ser declarado pelo participante |
| `capabilities[]` | `capabilities[].capability_id` | parcial | o identificador isolado não descreve semântica suficiente |
| `capability_offers[].input/output` | `input_contract` / `output_contract` | parcial | preservar schema e versão; digest é recomendado quando existir |
| `observable_success` | `evidence_requirements[]` | parcial | converter em requisitos verificáveis, sem copiar texto cegamente |
| método e endpoint da oferta | nenhum | deliberadamente incompatível | pertencem ao futuro binding ARC-02, não à capability |
| `mount_path` | nenhum | sem equivalente | detalhe da superfície HTTP vigente |
| `transport` | nenhum | sem equivalente | detalhe de implantação vigente |
| `technical_endpoints` | nenhum | sem equivalente | contrato técnico histórico permanece no subsistema v1 |
| headers de identidade/proxy | `subject_assertion` | não conversível diretamente | requer issuer, audience, validade e integridade verificáveis |
| health/readiness HTTP | `state_declarations` quando semanticamente útil | parcial | observação operacional e estado declarado não são a mesma afirmação |
| `data_ownership` | `authority_scopes` / `authority_boundaries` | exige enriquecimento | declarar escopo, responsável e não transferência |
| `audit_level` | `evidence_requirements` / `evidence_policy` | exige enriquecimento | definir evidência e custódia por capability/relação |
| `production_eligible` | nenhum | sem equivalente | draft semântico nunca concede elegibilidade operacional |
| aliases e códigos HTTP | nenhum | sem equivalente | permanecem apenas no binding legado |

## Capability

Uma oferta v1 só pode originar uma capability draft depois de declarar:

- propósito;
- contratos de entrada e saída;
- autoridade decisória;
- efeito observável;
- precondições;
- evidências requeridas.

Consequentemente, copiar apenas `capabilities[]` é insuficiente.

## Invocation

`sister.subsystem/1.0.0` descreve chamadas por método, endpoint, headers e
códigos de resposta. O draft de invocation descreve caller, participante alvo,
capability, finalidade, contrato, argumentos, prazo e contexto de identidade.

Não há conversão automática entre as duas representações. Um futuro adapter
ARC-02 deverá mapear uma operação explicitamente autorizada, sem expor ao
cliente uma invocação genérica irrestrita.

## Relation

O contrato v1 não representa uma relação completa. Acordos e registros atuais
podem fornecer evidência para uma proposta, mas uma relation draft requer:

- ao menos dois participantes e seus papéis;
- concessões direcionais de capabilities;
- finalidades permitidas;
- fronteiras de autoridade;
- governança e ciclo de vida;
- política de evidência e provenance.

Uma integração técnica existente não prova aceitação dessa relação.

## Critérios para futura migração

Uma migração só poderá ser proposta quando:

1. os drafts forem revisados e estabilizados por decisão posterior;
2. E3 demonstrar equivalência semântica entre dois bindings;
3. houver adapter explícito para o contrato v1, com falha fechada;
4. nenhum campo técnico for promovido a identidade da capability;
5. rollback preservar integralmente a baseline v1;
6. runtime e perfis forem alterados em missão separada e autorizada.
