# Base visual canônica do SisTer

Este diretório guarda a representação basal “Pessoa situada em um ambiente computacional”. A autoridade visual é [`reference.png`](./reference.png), preservada sem edição a partir do PNG aprovado.

## Contrato canônico

- Dimensão: **1672 × 941 px** (aproximadamente 16:9).
- Papel: referência visual estável para a experiência SisTer e para derivações gráficas futuras.
- Regra de precedência: quando texto e imagem divergirem, a imagem canônica vence.
- Continuidade espacial: núcleo humano-contextual, ecossistema computacional e território são uma composição única, não três painéis independentes.

## Arquivos

- `reference.png`: autoridade de comparação, imutável por convenção.
- `sister-experience-base.svg`: contêiner SVG versionável em dimensão canônica. Mantém o PNG local como camada visível de autoridade e expõe regiões semânticas nomeadas, geometria estável e uma transcrição vetorial editável, inicialmente oculta.
- `sister-experience-base.png`: renderização canônica do SVG.

O raster de referência permanece visível no SVG por uma decisão deliberada de fidelidade. A pesquisadora, a paisagem, as transparências compostas, os arcos e os microdetalhes não podem ser separados do arquivo-fonte sem inventar pixels. Isso aplica a regra de que fidelidade visual tem prioridade sobre vetorização. O SVG não incorpora o PNG como base64: ele o referencia localmente, mantendo revisão e substituição independentes.

## Componentes e grupos SVG

Os grupos de primeiro nível são `background`, `title`, `left-principles`, `ecosystem`, `territory`, `right-principles` e `footer-brand`. Dentro de `ecosystem` ficam `context-core`, `person`, `sister`, `urt`, `atmos`, `nexo` e `praxis`; as demais dimensões contextuais também têm regiões próprias (`role`, `project`, `activity`, `territory-context` e `period`).

Cada grupo registra um `data-bounds`, um título acessível e geometria transparente para interação. A classe `vector-transcription` contém texto real e editável, oculto no render canônico para não duplicar o texto já presente na autoridade raster. Essa camada pode ser ativada em derivações que substituam regiões raster de forma controlada.

## Projeção web funcional

A Home pública consome uma cópia byte-idêntica em `web/assets/sister-experience-reference.png`, necessária porque a imagem de runtime copia somente `web/`. O contrato automatizado impede que essa cópia divirja da autoridade. Em telas com mais de 1040 px, a composição canônica é preservada integralmente e recebe áreas HTML semânticas transparentes: os módulos abrem detalhes, os seis nós alteram o contexto ativo e as marcas SisTer encaminham para autenticação. No viewport canônico de 1672 × 941, a captura da Home é pixel a pixel idêntica à referência quando nenhum controle tem foco.

Em telas de até 1040 px, a experiência muda para uma projeção responsiva: a referência integral permanece visível, módulos e contextos viram cartões táteis, e todos os textos passam a ser HTML legível. Essa projeção não altera nem substitui a composição basal.

## Paleta extraída

| Uso | Cor de referência |
| --- | --- |
| Azul profundo / títulos | `#021D48` |
| Ciano / URT | `#008DA3` |
| Roxo / Atmos | `#6E489C` |
| Laranja / Nexo | `#CA7017` |
| Verde / Praxis | `#0B8542` |
| Gelo / fundo luminoso | `#EDF0F3` |
| Azul-cinza / névoa | `#D9E5EA` |
| Verde territorial | `#6A896C` |

As cores são amostras do PNG; gradientes, transparências e iluminação permanecem definidos pelos pixels canônicos.

## Tipografia

A aparência da referência é reproduzida pelo raster aprovado. A transcrição vetorial usa `Montserrat` com fallback para `Noto Sans` e `sans-serif`, por ser a família local mais próxima em largura, peso e desenho. Não se deve trocar a tipografia da imagem canônica silenciosamente.

## Regras de composição

1. Preservar o `viewBox="0 0 1672 941"`.
2. Não mover, redimensionar ou recolorir regiões sem gerar e inspecionar uma nova comparação.
3. Não substituir a pesquisadora nem a paisagem por conteúdo semelhante ou gerado.
4. Não transformar URT, Atmos, Nexo e Praxis em navegação estrutural; são participantes federados em órbita do contexto humano.
5. Preservar os rótulos, arcos, nós e relações semânticas como parte informacional da composição.
6. Criar derivações em novos arquivos; a referência e esta base permanecem estáveis.

## Renderização e comparação

Requisitos: Python 3, Pillow, NumPy e Firefox. O Firefox é usado em modo headless porque preserva corretamente a referência raster local vinculada pelo SVG. A partir da raiz do repositório:

```bash
python3 tools/visual-diff/compare.py
```

O comando renderiza o SVG em `sister-experience-base.png`, valida a dimensão e escreve em `tools/visual-diff/out/`:

- `diff.png`: diferença absoluta com contraste ampliado;
- `overlay-50.png`: sobreposição de referência e candidato a 50%;
- `metrics.json`: MAE, RMSE, PSNR, SSIM global, dHash e contagem de pixels alterados.

Para comparar outro candidato sem renderizá-lo:

```bash
python3 tools/visual-diff/compare.py --no-render --candidate caminho/para/candidato.png
```

O processo retorna código `0` apenas para equivalência pixel a pixel. Uma derivação visual pode usar as métricas como diagnóstico, mas sempre exige também inspeção humana da sobreposição.
