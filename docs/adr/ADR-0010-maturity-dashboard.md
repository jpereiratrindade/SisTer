# ADR-0010: Painel administrativo de maturidade

## Status

Aceita

Atualizada em 2026-07-31 para explicitar a evolução do painel para um Centro
de Engenharia do SisTer.

## Contexto

O SisTer possui gates executáveis de Pré-Alfa, Alfa, Beta, Gama e Produção.
Seus resultados precisam ser compreendidos pela equipe sem transformar a
interface web em uma segunda autoridade de avaliação ou em um mecanismo de
execução remota de comandos.

Expor relatórios brutos também seria inadequado: eles podem conter caminhos
locais, detalhes operacionais e saída não limitada. O painel precisa consumir
um contrato estável, sanitizado e produzido pelo próprio verificador.

## Decisão

Adotar o contrato `sister.maturity-status/1.0.0` como única fonte de dados do
Centro de Engenharia do SisTer, com as seguintes invariantes:

- `verify-sister-maturity.sh` permanece como autoridade sobre os gates;
- o painel é somente leitura e não calcula estados ou promoções;
- o navegador nunca inicia scripts, processos ou comandos;
- a publicação do status é atômica, validada e sanitizada;
- relatórios reais permanecem em `.run/maturity/` e não são versionados;
- a API lê somente caminhos fixos configurados pelo servidor;
- a primeira versão exige papel `admin`, migrando futuramente para a
  capacidade `sister.maturity.read`;
- caminhos absolutos, credenciais, cookies, tokens, variáveis de ambiente e
  saída bruta não podem integrar o contrato público;
- o histórico é limitado, sanitizado e ordenado por execução.

A interface administrativa pode apresentar projeções derivadas da evidência,
como síntese executiva, pipeline de gates, saúde da engenharia, diagnóstico de
promoção e leitura por subsistema. Essas projeções são explicativas: elas não
substituem os estados, bloqueios e resultados publicados pelo verificador.

## Consequências

- a equipe passa a consultar evidências de maturidade no plano administrativo;
- o painel passa a operar como centro de governança técnica, mantendo leitura
  executiva e rastreabilidade no mesmo lugar;
- uma falha do painel não altera o resultado do gate;
- atualizar a página apenas relê a evidência publicada;
- executar ou agendar gates continua responsabilidade do terminal, CI ou de
  uma unidade operacional aprovada;
- mudanças no formato exigem nova versão do schema e testes de compatibilidade;
- a API administrativa pode evoluir para persistência no PostgreSQL sem mudar
  a autoridade do verificador.
