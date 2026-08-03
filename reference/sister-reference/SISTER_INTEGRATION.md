# Subsistema de Referência SisTer

Identificador no registro: `sister_reference`.

Implementação mínima e controlada de `sister.subsystem/1.0.0`. Existe somente
para provar descoberta, saúde, identidade mediada, operação funcional, falhas
controladas e ciclo de vida. Escuta exclusivamente em `127.0.0.1:19001`, não
possui banco, gateway, frontend ou acesso LAN próprio.

API canônica: `GET /manifest`, `/health`, `/ready`, `/capabilities`, `/identity`
e `POST /echo`. Operações funcionais exigem mediação autenticada pelo SisTer.
