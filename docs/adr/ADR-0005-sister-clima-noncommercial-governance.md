# ADR-0005: Governança não comercial do Sister-Clima

## Status

Aceita

## Contexto

O Sister-Clima combina software GPLv3 com dados de fontes que possuem regimes
distintos. A API gratuita do Open-Meteo admite uso não comercial, incluindo
aplicações sem fins lucrativos sem assinaturas ou publicidade e pesquisa
pública em instituições públicas. Os dados do Open-Meteo são CC BY 4.0. NASA
POWER segue a política de dados abertos da NASA e requer preservação das
marcações aplicáveis e citação.

O SisTer já autentica a entrega do link, mas o Streamlit de origem não possui
autenticação própria. Apenas ocultar o endereço não constitui controle de
acesso quando a porta é exposta em rede.

## Decisão

Adotar o contrato `sister-clima.governance/1.0.0` com as seguintes invariantes:

- finalidade de pesquisa pública e institucional sem exploração comercial;
- audiência de usuários identificados;
- link entregue apenas após autenticação no SisTer;
- origem limitada a loopback até existir proxy ou controle de acesso próprio;
- proibição de assinatura, publicidade, revenda, promoção comercial e vantagem
  econômica;
- atribuição, licença, transformação, proveniência, operador e referência
  espacial em todo resultado promovido;
- revisão obrigatória diante de mudança de termos, fonte, cota, autenticação,
  exposição ou finalidade;
- preservação independente da GPL do software e das licenças dos dados.

## Consequências

- indicadores revisados e camadas exportadas podem chegar ao SisTer dentro da
  finalidade registrada;
- resultados derivados do Open-Meteo continuam restritos a usuários
  identificados e ao contexto não comercial;
- a URL do Sister-Clima não pode ser publicada nem exposta diretamente em rede;
- uma proposta remunerada ou comercial exige nova decisão e, para Open-Meteo,
  contratação compatível ou outra fonte;
- a ingestão automática futura deve validar o contrato e os metadados
  obrigatórios antes da promoção.
