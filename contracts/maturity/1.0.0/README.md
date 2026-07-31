# Contrato de maturidade 1.0.0

`sister.maturity-status/1.0.0` representa a última execução sanitizada dos
gates de maturidade. `sister.maturity-history/1.0.0` indexa até cem execuções
locais sem incorporar logs brutos.

O verificador é a autoridade sobre os resultados. Consumidores devem apenas
exibir os estados recebidos e rejeitar versões de schema desconhecidas.

Validação local:

```bash
python3 scripts/maturity/validate-status.py \
  contracts/maturity/1.0.0/example.json
```
