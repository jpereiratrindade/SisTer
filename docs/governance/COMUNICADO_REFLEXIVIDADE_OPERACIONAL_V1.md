# Comunicado à equipe — Reflexividade Operacional no SisTer

**Referência:** EFE-SisTer/1.4  
**Decisão em validação:** níveis e perfis de reflexividade  
**Primeiro piloto:** integração Nexo–Compras

## O que foi decidido

O SisTer passa a adotar formalmente o **Princípio da Reflexividade Operacional**:

> Toda função relevante deve produzir evidências suficientes para que o sistema avalie sua própria execução em relação ao propósito, aos contratos e às políticas vigentes, tornando divergências compreensíveis e ações corretivas governáveis.

## Por que esta comunicação acontece agora

Esta orientação deve ser conhecida pela equipe **antes do início da codificação**. A reflexividade altera o vocabulário do sistema, distribui responsabilidades e estabelece fronteiras de autoridade entre quem coleta evidências, quem avalia, quem autoriza e quem executa uma resposta.

O objetivo imediato não é implementar todo o modelo de reflexividade. É definir o terreno comum para que cada componente, subsistema ou equipe não construa seu próprio modelo de observação e correção. Sem esse alinhamento, diferentes “espelhos” podem produzir diagnósticos incompatíveis, duplicar autoridade e transformar a rastreabilidade em um labirinto operacional.

Esta comunicação, portanto, é uma decisão de arquitetura e governança que antecede a implementação. Ela fixa o vocabulário, as responsabilidades e as fronteiras mínimas; as capacidades serão materializadas progressivamente, por perfis, ADRs, contratos, testes e pilotos autorizados.

A reflexividade não será aplicada com um único nível global. Cada capacidade relevante terá um `ReflexivityProfile`, combinando:

- **profundidade D0–D5:** o que será avaliado;
- **autoridade A0–A5:** o que o sistema poderá fazer;
- **efeito operacional:** `shadow`, `pass`, `warn` ou `block`;
- **ações permitidas:** observar, recomendar, solicitar aprovação, cancelar, isolar, reverter, suspender ou reprocessar, conforme política explícita.

## O que não foi decidido

Esta decisão **não autoriza** o SisTer a alterar autonomamente:

- contratos e acordos;
- políticas de maturidade;
- critérios ou métodos científicos;
- código-fonte;
- finalidade dos subsistemas.

Mudanças dessa natureza permanecem sob decisão humana e processo formal de governança.

## Primeiro piloto

A integração **Nexo–Compras** começará com:

```text
profundidade: D2–D3
autoridade: A1
modo: shadow
efeito sobre a execução: nenhum
```

O piloto deverá:

1. congelar as referências aplicáveis;
2. capturar evidências da execução;
3. produzir `OperationalAssessment`;
4. classificar o resultado como `confirmed`, `divergent`, `inconclusive` ou `not_applicable`;
5. explicar a conclusão pelo `sisterctl`;
6. não bloquear nem corrigir automaticamente a execução.

## Direção de implementação em C++

A linha de base utilizará recursos estáveis de C++20/23:

- tipos fortes, `concepts`, `constexpr` e `consteval`;
- `std::variant` para estados tipificados;
- `std::expected` para resultados e falhas explícitas;
- RAII para garantir produção de evidência;
- `std::source_location` e `std::stacktrace` para reconstrução técnica;
- `std::jthread` e `std::stop_token` para cancelamento cooperativo.

Contratos, reflexão estática e `std::execution` do C++26 permanecerão em **laboratório**, atrás de interfaces estáveis, até haver ADR, suporte de compiladores e testes de portabilidade.

## Fronteira arquitetural obrigatória

O componente que avalia uma divergência não recebe automaticamente autoridade para corrigi-la.

```text
EvidenceCollector
        ↓
AssessmentEngine
        ↓
OperationalAssessment
        ↓
ReflexivityPolicy / autorização
        ↓
CorrectiveActionExecutor
```

Avaliação e execução corretiva deverão possuir interfaces, políticas, testes e registros separados.

## Próximas entregas

1. Revisar e aceitar a **EFE-SisTer/1.4**.
2. Abrir a **ADR-REF-01 — Níveis e Perfis de Reflexividade**.
3. Definir o schema `ReflexivityProfile/1.0.0`.
4. Implementar o perfil `RFP-NC-01` para Nexo–Compras.
5. Executar o piloto exclusivamente em `shadow`.
6. Avaliar evidências antes de qualquer evolução para A2, A3 ou A4.

## Síntese

> O SisTer deve nascer amplamente reflexivo, porém apenas seletivamente autocorretivo.

A comunicação desta decisão acontece antes da codificação porque alinha o vocabulário, as responsabilidades e as fronteiras de autoridade. Ela não representa ordem para implementar todo o modelo de uma vez; define o terreno comum e o experimento mínimo que sustentarão as próximas decisões sem criar espelhos locais que se transformem em labirintos.
