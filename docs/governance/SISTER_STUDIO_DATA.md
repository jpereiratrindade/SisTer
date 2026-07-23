# Governança de dados da integração Sister-Studio

## Oferta inicial

O SisTer recebe do Sister-Studio somente:

- identidade e versão do sistema e do contrato;
- capacidades e formatos de entrada e saída;
- disponibilidade sanitizada dos três módulos;
- horário da verificação.

Esses dados são `restricted` no endpoint administrativo. Uma visão pública
futura pode publicar apenas versão e estado agregado, após revisão.

## Valor para a evolução do SisTer

As informações mais úteis, em ordem de risco crescente, são:

1. grafo de capacidades e compatibilidade de formatos;
2. confiabilidade operacional por módulo;
3. proveniência técnica de fluxos, com IDs opacos e versões de algoritmos;
4. métricas agregadas de demanda, duração, rejeição e sucesso;
5. temas declarados voluntariamente para conexão com contextos territoriais.

Os itens 3 a 5 não estão implementados. Para publicação agregada deverão existir
faixas em vez de valores individualizantes, limiar mínimo de contribuições,
janela temporal adequada e teste documentado de reidentificação. Temas não
devem ser inferidos de voz, texto ou mídia por padrão.

## Exclusões

Permanecem privados no sistema produtor:

- identidade, sessão e arquivos de usuários;
- textos, prompts, roteiros e legendas;
- amostras e perfis vocais;
- mídia carregada ou gerada;
- projetos, caminhos, logs e auditoria detalhada.

Amostra vocal vinculada a pessoa exige proteção reforçada e pode entrar no
regime de dado biométrico sensível quando usada para identificação.

## LGPD e responsabilidade

O contrato não fixa controlador e operador. Cada implantação deve registrar
papéis, finalidades, bases autorizativas, retenção, atendimento ao titular,
suboperadores e resposta a incidentes. Uma nova exportação permanece proibida
até atualizar o inventário, o schema, a classificação e o registro da decisão.

Contrato técnico e justificativa arquitetural:

- `contracts/sister_studio_capabilities.schema.json`;
- `contracts/sister_studio_health.schema.json`;
- `docs/adr/ADR-0004-sister-studio-service-integration.md`.
