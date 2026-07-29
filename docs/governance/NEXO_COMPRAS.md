# Nexo e o contexto de compras

## Estado

- SisTer Nexo: integrado e governado;
- `cpp/sister_compras`: candidato à integração;
- `Nexo-Compras`: nome de produto em avaliação, ainda não adotado;
- inicialização pelo SisTer: não habilitada.

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

## Pendências antes da integração

1. mover o PostgreSQL do Compras para uma porta livre: `55435` pertence ao
   ambiente de teste do SisTer;
2. eliminar credenciais padrão versionadas e adotar configuração local não
   versionada;
3. alinhar contrato e aplicação, atualmente em versões diferentes;
4. definir saúde sanitizada e manifesto de sistema;
5. reutilizar a identidade autenticada do SisTer;
6. separar dados operacionais de exemplos versionados;
7. testar migração e rollback antes de qualquer renomeação.

## Critério para o nome Nexo-Compras

O nome será adotado somente se a integração representar uma extensão clara do
fluxo do Nexo sem reduzir a autonomia do contexto de compras. Repositório,
identificador, contratos, banco e histórico Git não devem ser renomeados em uma
única mudança irreversível.
