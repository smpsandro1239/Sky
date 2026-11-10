# ADR-002 — Stack tecnológica inicial

- **Estado:** Aceite como proposta de base; versões por fixar
- **Data:** 2026-11-10
- **Contexto:** O produto necessita de uma web app moderna, API tipada, persistência relacional e ambiente reproduzível.
- **Decisão:** Next.js, React e TypeScript no frontend; FastAPI e Python no backend; PostgreSQL e SQLAlchemy para persistência; Redis para cache; Docker Compose para desenvolvimento local; GitHub Actions para CI.
- **Consequências positivas:** Ecossistema maduro, separação clara de responsabilidades, ferramentas de teste e documentação disponíveis.
- **Consequências negativas:** Dois ecossistemas de linguagem e toolchains; necessidade de contratos claros entre frontend e API.
- **Condições:** Fixar versões compatíveis e estáveis durante a implementação. Não interpretar esta ADR como validação de versões específicas.
