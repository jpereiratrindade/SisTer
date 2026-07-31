# SisTer-Lab — ambiente experimental espelhado

O SisTer-Lab mantém snapshots verificáveis do `sisterd` e do `sisterctl`.

## Princípio

O código testado deve ser o mesmo código operacional. O laboratório altera
cenários, dados, dependências, topologia, carga e falhas — não cria uma segunda
implementação do sistema-alvo.

## Estrutura

```text
sisterd_lab/
├── target/
│   ├── sisterd/
│   └── sisterctl/
├── manifests/
│   ├── sisterd.sha256
│   ├── sisterctl.sha256
│   ├── target.sha256
│   └── snapshot.env
├── scripts/
│   ├── verify-identical.sh
│   ├── compare-with-upstream.sh
│   └── build-targets.sh
├── scenarios/
├── evidence/
├── config/
└── build/
```

## Verificações

Integridade interna do snapshot:

```bash
./scripts/verify-identical.sh
```

Comparação com as árvores operacionais de origem:

```bash
./scripts/compare-with-upstream.sh
```

Compilação dos dois alvos:

```bash
./scripts/build-targets.sh
```

## Regra de evidência

Uma execução experimental só deve ser considerada válida quando:

1. os manifestos SHA-256 forem válidos;
2. o commit ou estado da árvore de origem estiver registrado;
3. as diferenças ambientais estiverem declaradas;
4. o cenário for reproduzível;
5. as evidências forem armazenadas sem modificar o código-alvo.
