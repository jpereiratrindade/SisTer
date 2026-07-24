# Governança de dados e uso do Sister-Clima

## Finalidade autorizada

O Sister-Clima integra o SisTer para pesquisa pública, resiliência climática,
educação e apoio decisório institucional sem finalidade lucrativa ou
comercial. O contrato aplicável é `sister-clima.governance/1.0.0`, formalizado
por:

- `contracts/sister_clima_governance.schema.json`;
- `examples/sister_clima_governance_example.json`;
- `python/Sister-Clima/contracts/noncommercial_use_policy.json`.

A existência de instrumento de cooperação ou contrato institucional não muda,
por si só, essa classificação. Qualquer remuneração, vantagem econômica,
revenda, assinatura, publicidade, integração em produto comercial ou pesquisa
comercial não divulgada aciona revisão prévia da governança e das licenças.

## Identidade e acesso

- somente usuários identificados e autenticados no SisTer recebem o link;
- a URL direta não é publicada no catálogo público;
- a aplicação de origem permanece em `127.0.0.1` enquanto não houver proteção
  própria ou proxy reverso autenticado;
- expor a porta do Sister-Clima em rede sem esse controle é proibido;
- parâmetros de sessão, autenticação, rede e logs não são compartilhados.

A autenticação do SisTer protege a entrega do link, não a porta de origem. Uma
implantação em rede deve impedir que o endereço do Streamlit contorne o controle
de identidade.

## Fontes e obrigações

### Open-Meteo

- a API gratuita é usada somente no contexto não comercial admitido pelos
  termos, inclusive pesquisa pública em instituição pública;
- devem ser respeitados os limites vigentes do serviço;
- os dados permanecem sob CC BY 4.0;
- toda apresentação ou exportação deve atribuir Open-Meteo, incluir link para a
  licença e indicar processamento ou modificação;
- não há garantia de disponibilidade, completude ou adequação decisória.

Referências normativas:

- <https://open-meteo.com/en/terms>
- <https://open-meteo.com/en/license>

### NASA POWER

- os dados NASA são tratados conforme a política NASA Earthdata e eventuais
  marcações específicas do produto;
- NASA POWER deve ser citada como fonte;
- a apresentação não pode sugerir endosso da NASA;
- conteúdo de terceiros eventualmente identificado preserva sua licença.

Referência normativa:

- <https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy>

### IPWhois

- usado somente após ação explícita no card e apenas quando o acesso HTTP não
  permite a geolocalização protegida do navegador;
- fornece uma aproximação por IP, que pode apontar para a rede ou provedor em
  vez da posição real da pessoa;
- latitude e longitude são reduzidas antes da consulta climática;
- o SisTer não persiste IP, coordenadas ou resposta de localização;
- o serviço externo recebe a requisição e aplica seus próprios termos e
  política de privacidade;
- seu uso deve ser revisto pela instância institucional de privacidade antes de
  uma implantação de produção.

Referências normativas:

- <https://ipwhois.io/documentation>
- <https://ipwhois.io/terms>
- <https://ipwhois.io/privacy>

## Resultados que podem chegar ao SisTer

Somente após revisão:

- indicadores climáticos;
- camadas espaciais explicitamente exportadas;
- cobertura temporal;
- proveniência das fontes.

Cada resultado deve conter, no mínimo:

- fonte, URL, licença e atribuição;
- indicação das transformações;
- instante de coleta e cobertura temporal;
- referência espacial e método de processamento;
- operador responsável e versão do schema.

Respostas brutas de APIs, indicadores não revisados, parâmetros de sessão,
configuração de rede, dados de autenticação e logs não são promovidos.

### Prévia local transitória

O card autenticado pode apresentar uma prévia não promovida do acumulado
modelado de precipitação:

- somente após ação explícita da pessoa usuária;
- por geolocalização autorizada do navegador em HTTPS ou localização aproximada
  por IP, claramente informada, quando o acesso HTTP bloquear o recurso;
- com latitude e longitude reduzidas a duas casas decimais antes da consulta;
- por chamada direta e transitória à API Open-Meteo;
- sem persistência das coordenadas ou da resposta no SisTer;
- com fonte, período e natureza estimada identificados na interface.

A prévia permanece classificada como resultado restrito e não revisado. Ela não
integra o catálogo territorial, o repositório de evidências nem deve fundamentar
sozinha alertas ou decisões operacionais.

## Software

O Sister-Clima permanece GPL-3.0-or-later. Prestação remunerada de
desenvolvimento ou suporte é permitida, mas a distribuição do programa deve
preservar o copyleft e entregar o código-fonte correspondente nas condições da
GPL. A licença do programa não substitui as licenças e os termos das fontes de
dados.

## Revisão obrigatória

O responsável pela integração deve suspender a promoção de novos resultados e
solicitar revisão quando ocorrer:

- alteração dos termos de uma fonte;
- inclusão de nova fonte;
- mudança da exposição em rede ou da autenticação;
- ultrapassagem das cotas da API;
- proposta de remuneração, vantagem econômica, revenda ou uso comercial.
