# Alinhamento normativo com a EFE-SisTer/1.2

**Referência:** EFE-SisTer/1.2 — *Especificação Funcional e de Engenharia do SisTer*

**Data da referência:** 1 de agosto de 2026

**Status da referência:** versão revisada para validação

**SHA-256 do documento recebido:** `d04c76f4980c861c7717990f2339d86f9681bec6790d77059e5bef4e5f24a410`

## Autoridade e escopo

A EFE-SisTer/1.2 substitui a EFE-SisTer/1.1 como referência funcional e de
engenharia corrente. Ela é normativa para o modelo-alvo e descritiva somente
quanto ao snapshot de código que inspecionou. ADRs, contratos, procedimentos e
evidências continuam sendo artefatos próprios e devem permanecer alinhados à
EFE.

A revisão 1.2 formaliza a cadeia de segurança:

```text
ameaça → requisito → controle → implementação → teste → evidência
       → risco residual → maturidade
```

Código defensivo isolado não encerra uma ameaça. A promoção requer teste
reproduzível, evidência válida, risco residual explícito e autoridade definida.

## Consequências para o ciclo atual

1. SEC-01C e SEC-01D são publicados na release `v0.2.6`, sem mover nem recriar
   tags anteriores.
2. O MAES-SisTer/1.0 é publicado na mesma baseline como registro operacional
   versionado de ativos, fronteiras, ameaças, controles, testes, evidências,
   riscos residuais, responsáveis, estados e datas de revisão.
3. SEC-02V validou o candidato posterior à `v0.2.6`. SEC-02M restringiu sua
   promoção a uma flag própria e a uma rota exata. A `v0.2.7` publica somente a
   leitura interna e shadow coordenada com o Nexo; escrita e exposição externa
   continuam bloqueadas.
4. SEC-03 permanece posterior ao SEC-02 e responsável pelo gateway
   especializado. Nenhuma etapa autoriza transformar o `sisterd` em servidor
   HTTP público.

## Rastreabilidade imediata

| Entrega | Ameaças iniciais relacionadas | Controle/evidência atual | Próximo gate |
|---|---|---|---|
| SEC-01C | `TH-HTTP-01`, `TH-HTTP-03`, `TH-CXX-01`, `TH-CXX-02` | parsing estrito, limites, barreira por job e suíte hostil em `docs/evidence/security/SEC-01C-01D.md` | publicação imutável da `v0.2.6` |
| SEC-01D | `TH-AUTH-01`, `TH-HTTP-03`, `TH-AUD-01` | limites multidimensionais, armazenamento limitado, `429`, métricas e testes concorrentes | publicação imutável da `v0.2.6` |
| SEC-02 | `TH-IDENT-01`, `TH-AUTHZ-01`, `TH-AUD-01` | publicado na `v0.2.7` para uma rota exata, leitura interna e shadow; `TH-IDENT-01` parcial pelo replay após reinício e operação manual de chaves | SEC-02R antes de escrita; SEC-03 antes de exposição externa |
| SEC-03 | `TH-HTTP-02`, `TH-HTTP-03`, `TH-HTTP-04`, `TH-WS-01`, `TH-PROXY-01`, `TH-PROXY-02` | ainda não implementado | ADR do gateway, testes negativos e risco residual |

## Regra de promoção

A sequência aprovada é:

```text
publicar SEC-01C/SEC-01D como v0.2.6 ─┐
                                     ├→ validar formalmente SEC-02 (SEC-02V)
criar e revisar MAES-SisTer/1.0 ─────┘
→ publicar SEC-02 como v0.2.7 com política exata
→ implantar a leitura shadow de forma controlada
→ implementar e validar SEC-03
```

Enquanto essa sequência não for concluída, o `sisterd` permanece plano de
controle interno em loopback, com proxies legados e WebSocket proibidos em
produção.
