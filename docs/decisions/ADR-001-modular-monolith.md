# ADR-001 — Monólito modular

- **Estado:** Aceite
- **Data:** 2026-11-10
- **Contexto:** O SKY começa com uma equipa e produto em fase inicial. Microserviços aumentariam custos de operação, observabilidade, deploy e coordenação antes de existir escala que os justifique.
- **Decisão:** Implementar inicialmente um backend monolítico organizado em módulos de domínio, com contratos internos e adaptadores para integrações externas.
- **Consequências positivas:** Menor complexidade operacional, transações locais mais simples, desenvolvimento e testes mais diretos.
- **Consequências negativas:** Exige disciplina para impedir acoplamento entre módulos; escalabilidade independente é limitada.
- **Revisão:** Reavaliar apenas com métricas e necessidades concretas de escala, disponibilidade ou autonomia de deploy.
