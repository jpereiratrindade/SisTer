# ADR-0009 — Perfis de usuário, grupos de pesquisa e controle de acesso

- Estado: aceito e em implementação
- Data: 2026-07-29

## Contexto

A plataforma SisTer e seus subsistemas federados (como SisTer Nexo para gestão científica e MorfoCampo/SisTer-Campo para dados territoriais) exigem controle de acesso para dados públicos, restritos e privados (`public_scope`).

Apenas definir escopos sem perfis de usuário e associação a grupos de pesquisa impede que a plataforma diferencie acesso anônimo, membros cadastrados, pesquisadores vinculados a projetos específicos, coordenadores científicos e administradores.

## Decisão

1. **Perfis Globais (RBAC)**:
   A plataforma define os seguintes perfis globais na tabela `sister_users`:
   - `guest`: Visitante não autenticado (acesso restrito a `public_scope = 'public'`).
   - `registered_user`: Usuário autenticado na plataforma (acesso a `public` e dados de interação da comunidade).
   - `researcher`: Pesquisador cadastrado e apto a integrar grupos de projetos de pesquisa.
   - `project_lead`: Liderança científica com capacidade de coordenação de grupos de pesquisa.
   - `admin`: Gestão técnica da plataforma e federação.

2. **Grupos de Projetos de Pesquisa (ReBAC)**:
   Os usuários são vinculados a **Grupos de Projetos de Pesquisa** (`sister_project_groups`) através da tabela associativa `sister_group_members`, possuindo papéis específicos dentro de cada grupo (`coordinator`, `researcher`, `collaborator`, `observer`).

3. **Resolução de Visibilidade por Conteúdo**:
   A visibilidade de um recurso (evidências, pacotes, artefatos de conhecimento) é resolvida avaliando:
   - `public`: Acessível por qualquer perfil (incluindo `guest`).
   - `restricted`: Acessível por usuários autenticados (`registered_user`, `researcher`, `admin`).
   - `private`: Acessível **apenas** por membros do grupo de projeto proprietário (`project_group_id`) ou administradores do sistema.

4. **Propagação de Identidade e Contratos**:
   O SisTer Core define o contrato `user_identity.schema.json` para compartilhamento seguro de metadados de identidade e pertinência a grupos entre os nós federados.

## Consequências

- Acesso a dados de pesquisa respeita a autonomia e privacidade dos projetos científicos.
- Permite que um pesquisador atue como coordenador em um grupo e colaborador em outro.
- Preserva a conformidade com a LGPD e políticas de dados sensíveis descritas em `PUBLIC_PRIVATE_SCOPE.md`.
- Garante base consistente para evolução das APIs e interfaces estáticas (`web/login.js`, `sisterd`).
