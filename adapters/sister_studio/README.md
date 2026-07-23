# Adaptador Sister-Studio

O `sisterd` consome o contrato `sister-studio.integration/1.0.0` por HTTPS.
Nesta fase, o adaptador lê somente catálogo de capacidades e saúde sanitizada.
Ele não envia trabalhos nem copia conteúdo.

## Configuração

O operador provisiona, fora do repositório:

```bash
export SISTER_STUDIO_TOKEN_FILE=/caminho/protegido/sister-integration.token
export SISTER_STUDIO_CA_FILE=/caminho/protegido/ca.crt
export SISTER_STUDIO_HOST=127.0.0.1
export SISTER_STUDIO_PORT=8443
```

`TOKEN_FILE` e `CA_FILE` são obrigatórios. Host e porta usam os valores acima
quando omitidos. O cliente exige TLS 1.2 ou superior, valida a cadeia e confirma
que o certificado pertence ao host configurado. Não há opção de desabilitar a
verificação.

Após autenticar como administrador no SisTer:

```text
GET /api/integrations/sister-studio
```

Erros retornam apenas códigos sanitizados; tokens, caminhos e mensagens brutas
da biblioteca TLS não são expostos.

Schemas: `contracts/sister_studio_capabilities.schema.json` e
`contracts/sister_studio_health.schema.json`.
