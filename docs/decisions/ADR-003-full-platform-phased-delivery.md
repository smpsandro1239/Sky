# ADR-003 — Plataforma integral com entrega faseada

- **Estado:** Aceite
- **Data:** 2026-11-10
- **Contexto:** O objetivo do SKY é evoluir para uma plataforma integral de viagens. Excluir reservas e pagamentos da visão limitaria a arquitetura e o produto.
- **Decisão:** Conceber desde o início a visão integral — descoberta, comparação, planeamento, reservas, pagamentos e pós-venda — mas implementar por fases. O MVP concentra-se em pesquisa, comparação, recomendações, favoritos, histórico/alertas e planeamento inicial.
- **Consequências positivas:** Visão de produto coerente e entrega incremental; evita construir fluxos financeiros antes de validar pesquisa e recomendações.
- **Consequências negativas:** Algumas decisões de arquitetura devem antecipar necessidades futuras sem implementar complexidade prematura.
- **Requisitos para a fase futura:** Estados de reserva explícitos, idempotência, webhooks autenticados, auditoria, reconciliação e prestador de pagamentos. Não armazenar dados completos de cartões.
