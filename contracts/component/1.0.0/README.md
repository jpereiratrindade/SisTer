# sister.component/1.0.0

Contrato normativo de **componente composável de implantação**.

Este contrato é deliberadamente diferente de `sister.participant/2.0.0`:

- `participant` descreve identidade, autoridade, capacidades e relações;
- `component` descreve como uma árvore de código pode ser qualificada e operada;
- a composição de implantação atribui bindings locais;
- a política de implantação decide elegibilidade e admissão;
- a release registra o resultado resolvido e verificável.

## Princípios

- nenhuma porta, host, endereço ou URL de implantação no descritor;
- nenhuma autorização ou elegibilidade de implantação é autodeclarada;
- nenhum comando shell arbitrário;
- drivers de build/teste são tipados e versionados;
- caminhos são relativos e não podem escapar do repositório;
- componentes `system` declaram contrato semântico e runtime instalado;
- `control_plane` pode ser `source-only/1`.

A localização canônica do descritor em cada repositório será:

```text
.sister/component.json
```

O descritor pertence ao sistema.

A decisão de compô-lo, sua elegibilidade naquele contexto e o binding concreto
pertencem à implantação.

Em particular:

```text
autodescrição != auto-admissão
compatibilidade != autorização
binding != identidade
```
