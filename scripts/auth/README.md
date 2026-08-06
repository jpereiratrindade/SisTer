# Administração local de usuários

O PostgreSQL do ambiente é a fonte autoritativa dos usuários do SisTer. O comando `userctl.sh` cria e administra contas e exporta um cache TSV restrito para a execução atual do `sisterd`.

```bash
./scripts/auth/userctl.sh --environment test list
./scripts/auth/userctl.sh --environment test create usuario@example.org "Nome" admin
./scripts/auth/userctl.sh --environment test password usuario@example.org
./scripts/auth/userctl.sh --environment test sync-runtime
```

O cache não deve ser editado manualmente. O gateway LAN o regenera antes de iniciar o `sisterd`.
