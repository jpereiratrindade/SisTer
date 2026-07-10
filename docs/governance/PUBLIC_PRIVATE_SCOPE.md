# Escopo Publico e Privado

## Objetivo

Definir o que o SisTer pode expor publicamente, o que deve circular de forma restrita e o que deve permanecer privado.

Esta politica orienta interface, API, banco de dados, relatorios, dashboards e pacotes de integracao.

## Classes de exposicao

### Publico

Pode aparecer em dashboards, relatorios abertos e material institucional.

Exemplos:

- lista de sistemas federados participantes;
- status agregado de servicos;
- versoes de contratos;
- indicadores agregados de integracao;
- camadas territoriais generalizadas ou anonimizadas;
- documentacao de governanca;
- metricas de qualidade sem dados pessoais ou sensiveis.

### Restrito

Pode circular entre equipe, parceiros autorizados ou ambientes autenticados.

Exemplos:

- pacotes CampoSync importados;
- relatorios de validacao;
- diagnosticos tecnicos detalhados;
- objetos territoriais com precisao operacional;
- metadados de evidencias;
- logs de integracao;
- embeddings de artefatos internos;
- resultados de similaridade semantica.

### Privado

Exige controle de acesso, finalidade explicita, minimizacao e trilha de auditoria.

Exemplos:

- dados pessoais;
- dados sensiveis;
- coordenadas de areas privadas quando identificaveis;
- fotos, audios ou documentos brutos;
- credenciais, tokens e secrets;
- logs com identificadores pessoais;
- evidencias que possam expor pessoas, propriedades ou operacoes sensiveis;
- embeddings derivados de conteudo privado quando puderem reter informacao sensivel.

## Regra padrao

Quando houver duvida, classificar como `private` ate revisao humana.

## Matriz inicial

| Artefato | Padrao | Observacao |
| --- | --- | --- |
| Contratos JSON Schema | Publico | Sem dados operacionais. |
| Manifesto de sistema | Publico ou restrito | Publico quando nao revelar detalhe sensivel de operacao. |
| Pacote CampoSync | Restrito | Pode conter dados territoriais e evidencias. |
| Evidencia bruta | Privado | Fotos, audios, documentos e logs devem ser protegidos. |
| Metadado de evidencia | Restrito | Publicar apenas agregado ou anonimizado. |
| Objeto territorial preciso | Restrito | Publico somente se generalizado, autorizado ou anonimizado. |
| Indicador agregado | Publico | Desde que nao reidentifique pessoas, propriedades ou operacoes. |
| Embedding | Restrito ou privado | Depende da origem do conteudo vetorizado. |
| Diagnostico de servico | Publico ou restrito | Publico para status agregado; restrito para falhas exploraveis. |
| Auditoria | Privado | Exposicao apenas para responsaveis autorizados. |

## Fronteira por sistema

Cada manifesto de sistema deve declarar:

- o que pode ser compartilhado com o SisTer;
- o que deve permanecer nativo e ser explorado na propria plataforma;
- quais resultados podem ser publicos;
- quais resultados sao restritos;
- quais artefatos sao privados;
- quais temas devem ser tratados como sensiveis;
- qual link de acesso direto pode ser exibido pela interface.

O SisTer pode apontar para a plataforma original, mas nao deve copiar ou expor funcionalidades que pertencem ao sistema federado quando isso quebrar autonomia, seguranca, LGPD ou responsabilidade tecnica.

## Cadeia dado, informacao, conhecimento e sabedoria

O SisTer adota a relacao DIKW como linguagem de integracao:

- `Dado`: aquilo que o SisTer recebe por contrato, mesmo que o sistema produtor ja trate como informacao.
- `Informacao`: dado validado, contextualizado e relacionado pelo SisTer.
- `Conhecimento`: interpretacao territorial resultante de cruzamento, recorrencia, historico, evidencia e contexto.
- `Sabedoria`: apoio decisorio governado, com limites, responsabilidade, transparencia e criterio de uso.

Essa cadeia nao autoriza exposicao automatica. Cada passagem precisa respeitar proveniencia, finalidade, escopo publico/restrito/privado e classificacao de temas sensiveis.

## LGPD

Diretrizes iniciais:

- finalidade explicita para coleta, transformacao e exposicao;
- minimizacao de dados pessoais;
- separacao entre dado bruto e indicador agregado;
- controle de acesso para dados privados;
- trilha de auditoria para acesso e transformacao;
- revisao antes de publicar geometrias, imagens, audios, documentos ou embeddings derivados de conteudo sensivel.

## Interface e API

Por padrao:

- home e dashboards devem usar dados `public` ou agregados;
- diagnostico tecnico publico deve esconder detalhes exploraveis;
- evidencias privadas nao devem ser exibidas diretamente;
- API deve filtrar por escopo e perfil de acesso;
- exports devem registrar classificacao de exposicao.

## Banco de dados

Tabelas operacionais devem possuir `public_scope`.

Valores planejados:

- `public`;
- `restricted`;
- `private`.

Consultas de dashboard devem filtrar explicitamente o escopo permitido.

## API

Endpoints publicos ou semi-publicos devem retornar apenas:

- dados `public`;
- agregados que nao permitam reidentificacao;
- diagnosticos que nao exponham falhas exploraveis;
- links de acesso autorizados pelos manifestos dos sistemas.

Endpoints internos ou autenticados poderao acessar dados `restricted` quando houver finalidade operacional clara. Dados `private` exigem controle de acesso, auditoria e justificativa.

Enquanto nao houver autenticacao implementada, o `sisterd` deve ser considerado servidor local/de desenvolvimento.
