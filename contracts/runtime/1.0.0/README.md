# sister.runtime/1.0.0

Contrato normativo para o **runtime instalado** de um componente SisTer.

Ele não descreve identidade, autoridade, relações ou capacidades semânticas do
participante. Também não contém endereço, porta, host público, socket, URL,
protocolo de transporte ou decisões de gateway. Essas informações pertencem à
implantação.

## Interface mínima

O `entrypoint` representa uma interface operacional tipada.

Deve aceitar obrigatoriamente:

- `start`
- `stop`
- `restart`
- `status`
- `health`

Pode ainda oferecer:

- `readiness`

Essas ações são semânticas, e não protocolos de transporte.

`health` significa avaliar a saúde do runtime instalado. O contrato não
determina se essa avaliação usa HTTP, socket Unix, IPC, processo local ou outra
técnica.

`readiness`, quando presente, indica que a implantação deve validá-la antes de
considerar o componente pronto para receber relações ou tráfego.

## Invariantes

1. `start` não compila nem executa testes;
2. o runtime usa somente artefatos previamente qualificados;
3. `start` e `stop` são idempotentes;
4. estado persistente não pertence à release;
5. `health` é obrigatório;
6. `readiness` é opcional e declarativa;
7. nenhuma ação declara binding local;
8. nenhuma ação implica autorização de implantação.

O binding efetivo é fornecido pelo resolvedor de composição da implantação.

```text
runtime
    declara operações

deployment
    fornece binding

policy
    decide admissão
```
