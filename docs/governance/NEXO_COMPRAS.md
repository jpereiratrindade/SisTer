# Nexo e o contexto de compras

## Estado

- SisTer Nexo: integrado e governado;
- `Nexo-Compras`: contexto autônomo integrado ao Nexo;
- identificador técnico preservado: `sister_compras`;
- inicialização pelo orquestrador raiz: habilitada como dependência do Nexo;
- acesso: `/integrations/nexo/compras/`.

## Relação de domínio

O vínculo nasce em uma necessidade de projeto:

```text
Projeto Nexo
  └── ação ou atividade
        └── necessidade de recurso
              └── Compras
                    ├── requisitos
                    ├── alternativas e cotações
                    ├── parecer e decisão humana
                    └── atendimento e entrega
```

O Nexo mantém o significado científico e operacional da atividade. O Compras
mantém a engenharia da aquisição. A integração devolve ao Nexo somente estados
e referências contratados; dados financeiros detalhados, fornecedores,
documentos comerciais e trilhas internas permanecem restritos.

## Identificadores mínimos

- `project_id`: projeto conhecido pelo Nexo;
- `research_activity_id`: atividade da estrutura científica, quando aplicável;
- `activity_id`: ação operacional que originou a demanda;
- `need_id`: necessidade pertencente ao Compras;
- `decision_id`: decisão humana rastreável;
- `evidence_refs`: referências aprovadas, sem copiar anexos privados.

Referências não autorizam acesso direto ao banco de origem. Exclusão ou
arquivamento em um contexto deve produzir estado contratual, nunca cascata
entre bancos.

## Implementação da fronteira

1. o SisTer autentica e encaminha a requisição ao Nexo;
2. o Nexo encaminha ao Compras somente pela rota interna `/compras/`;
3. o Compras consulta projetos e atividades na API contratual do Nexo;
4. o PostgreSQL do Compras usa porta `55440`, container e volume exclusivos;
5. configuração secreta e dados operacionais não são versionados;
6. a migração preservou os registros e manteve o volume anterior para rollback.

## Acordo operacional

Nexo e Compras mantêm cópias independentes do mesmo
`IntegrationAgreement`. A interface de cada sistema permite propor, negociar
capacidades, aceitar, ativar, suspender e revogar. Cada transição produz evento
local e, quando aplicável, recibo correlacionado por `agreement_id`, revisão e
digest SHA-256.

O acordo segue `sister.integration-agreement/1.0.0`; a relação concreta segue
`nexo-compras.profile/1.0.0`. As APIs e os schemas descrevem **como** comunicar;
o Aggregate bilateral determina **se**, **em que estado** e **com quais
capacidades** a comunicação é permitida.

## Do dado à informação

Uma necessidade recebida do Compras continua sendo dado para o Nexo. Ela se
torna informação quando o Nexo a relaciona ao projeto e às atividades que
explicam sua finalidade, verifica a qualidade das referências, interpreta sua
fase e explicita impacto, atenção e próxima ação.

O Nexo não infere vínculos inexistentes. Quando projeto ou atividade não podem
ser confirmados, a informação gerada é precisamente a pendência de
rastreabilidade. A projeção mantém proveniência do acordo e preserva o dado
original sem receber fornecedores, preços ou documentos comerciais.

## Identidade do produto

**Nexo-Compras** é o nome adotado para explicitar que compras é uma extensão
contratual do fluxo do Nexo. Repositório, identificador técnico, banco e
histórico Git permanecem estáveis. O Compras não aparece como subsistema direto
do SisTer.
