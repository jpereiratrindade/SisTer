# ADR-0016: Autorização por capacidades com negação por padrão

## Status

Aceita

## Contexto

A quarentena de transporte impede que o `sisterd` opere como borda pública,
mas não determina o que cada identidade autenticada pode fazer. A linha de base
possuía um catálogo de capacidades por papel, enquanto as integrações aceitavam
qualquer usuário autenticado e as rotas administrativas verificavam o papel
`admin` diretamente. O catálogo era informativo, não uma política executável.

## Decisão

O `sisterd` aplica autorização por capacidade antes de executar qualquer rota
sensível. A política inicial associa capacidades a papéis existentes, com
negação por padrão para papéis desconhecidos, capacidades ausentes e APIs sem
política declarada.

Mapeamentos críticos:

| Recurso | Capacidade | Finalidade |
|---|---|---|
| Sister-Clima | `climate.dashboard.read` | pesquisa pública não comercial |
| SisTer Nexo | `nexo.projects.read` | operações de pesquisa |
| Administração de usuários | `identity.users.manage` | administração de identidades |
| Evidências de maturidade | `maturity.evidence.read` | governança de engenharia |

As APIs de sistemas, contratos, evidências, diagnóstico e clientes internos
também declaram capacidades próprias. Uma API autenticada sem mapeamento é
negada em vez de herdar autorização administrativa implícita.

Cada decisão produz evento estruturado com instante, `request_id`, ator, papel,
capacidade, recurso, finalidade, resultado e motivo.

## Invariantes

- Requisição sem autenticação recebe `401`.
- Identidade sem a capacidade exigida recebe `403`.
- Capacidade não declarada e papel desconhecido falham fechados.
- Erros ou ausência de política nunca resultam em permissão.
- Gateway e interface não substituem a decisão feita pelo plano de controle.
- A autorização ocorre antes de qualquer conexão com o subsistema.
- Permissões e negações são auditáveis pelo mesmo `request_id` da requisição.

## Consequências

- O catálogo retornado por `/api/me/capabilities` passa a representar decisões
  efetivamente aplicadas pelo servidor.
- Usuários genéricos mantêm somente acesso à própria sessão; pesquisadores e
  líderes de projeto recebem as capacidades de integração definidas.
- O modelo inicial ainda deriva capacidades de papéis persistidos no arquivo de
  autenticação. Políticas por finalidade, escopo, risco e acordo bilateral
  exigirão armazenamento e contratos próprios.
- Antes de reativar integrações em produção, a identidade encaminhada deverá ser
  substituída por asserção interna assinada, curta e restrita à audiência.
