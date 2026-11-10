# SKY — Intelligent Travel Platform

**Discover better. Compare smarter. Travel further.**

O SKY é uma plataforma inteligente de descoberta, comparação e planeamento de viagens. O objetivo é ajudar cada cliente a encontrar as melhores opções de voos e alojamentos, considerando preço total, qualidade, localização, conveniência, condições e preferências pessoais.

A visão de longo prazo é uma plataforma integral de viagens, incluindo descoberta, comparação, planeamento, reservas, pagamentos e acompanhamento pós-compra. O princípio central é recomendar a melhor opção para cada pessoa — não apenas a mais barata — e explicar os motivos da recomendação.

## Estado do projeto

**Estado atual: Fases 1 e 2 concluídas.** A visão do produto, o âmbito inicial, a arquitetura e a documentação técnica de base estão concluídos. A implementação da plataforma é a etapa seguinte. Os serviços Docker, APIs, integrações e interfaces só devem ser considerados disponíveis quando estiverem efetivamente implementados e testados.

| Área | Estado |
|---|---|
| Fase 1 — visão e âmbito do produto | Concluída |
| Fase 2 — arquitetura, documentação e SKY Design System | Concluída |
| Arquitetura técnica | Documentada |
| Documentação técnica inicial | Concluída |
| Frontend e backend | Por implementar (fase seguinte) |
| Base de dados e Docker | Por implementar (fase seguinte) |
| Integrações externas | Por selecionar |
| Reservas e pagamentos | Fase futura |

## Produto e roadmap funcional

### MVP
- Pesquisa de voos e alojamentos.
- Comparação multicritério de resultados.
- Recommendation Engine com explicação dos critérios.
- Favoritos e histórico de pesquisas.
- Alertas e acompanhamento de preços, sujeitos à disponibilidade de dados dos fornecedores.
- Planeamento inicial de viagens.

### Evolução posterior
- Planeador avançado e itinerários.
- Reservas de voos e hotéis.
- Gestão de reservas e alterações.
- Pagamentos, cancelamentos e reembolsos.
- Notificações e acompanhamento pós-compra.

A arquitetura deve acomodar a evolução para reservas e pagamentos desde o início, mas estes fluxos não fazem parte do MVP. O SKY não armazenará dados completos de cartões; os pagamentos serão delegados a prestadores especializados.

## Arquitetura tecnológica proposta

| Camada | Tecnologia |
|---|---|
| Web | Next.js, React, TypeScript |
| UI e estilos | Tailwind CSS, shadcn/ui |
| API | Python, FastAPI, Pydantic |
| Persistência | PostgreSQL, SQLAlchemy |
| Cache | Redis |
| Mapas | MapLibre GL |
| Gráficos | Recharts |
| Ícones e tipografia | Lucide, Inter |
| Animações | Motion |
| Ambiente | Docker, Docker Compose |
| Testes | Pytest, HTTPX, Vitest, Playwright |
| CI/CD | GitHub Actions |

As versões serão fixadas num momento próprio, depois de verificar compatibilidade e versões estáveis. A arquitetura inicial será um **monólito modular**, evitando microserviços prematuros.

## Estrutura prevista do monorepo

```text
sky/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── design-tokens/
│   ├── ui/
│   └── shared-types/
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   └── monitoring/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── decisions/
│   ├── design/
│   └── security/
├── scripts/
├── .github/workflows/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Design System

Direção: **Premium Travel Tech** — tecnologia moderna, interface elegante, minimalista, acessível e mobile-first.

| Token | Cor | Aplicação |
|---|---|---|
| Midnight Navy | `#101D35` | Identidade e superfícies escuras |
| Sky Blue | `#2563EB` | Ações principais |
| Electric Sky | `#38BDF8` | Destaques e estados ativos |
| Cloud White | `#F5F7FB` | Fundos claros |
| Success Green | `#10B981` | Estados positivos |
| Amber | `#F59E0B` | Avisos |

Consultar [SKY Design System](docs/design/SKY_DESIGN_SYSTEM.md).

## Documentação

- [Arquitetura do sistema](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Arquitetura frontend](docs/architecture/FRONTEND.md)
- [Arquitetura backend](docs/architecture/BACKEND.md)
- [Modelo de dados](docs/database/DATABASE.md)
- [Contrato e convenções da API](docs/api/API.md)
- [Segurança](docs/security/SECURITY.md)
- [Decisões técnicas](docs/decisions/)

## Princípios do projeto

1. Recomendações explicáveis e comparações transparentes.
2. Preço total, condições e qualidade — não apenas preço anunciado.
3. APIs oficiais e fornecedores autorizados; evitar dependência de scraping.
4. Separação entre domínio de negócio e fornecedores externos.
5. Privacidade, segurança, acessibilidade e testes desde o início.
6. Distinguir sempre funcionalidades planeadas das implementadas.

## Roadmap técnico

- [x] **Fase 1 — descoberta e definição do produto:** visão, objetivos, âmbito e funcionalidades prioritárias.
- [x] **Fase 2 — arquitetura e documentação:** arquitetura, contratos e convenções, segurança, modelo de dados, decisões técnicas e SKY Design System.
- [ ] **Fase 3 — fundações do projeto:** monorepo, Docker Compose, configuração local e estrutura inicial de frontend e backend.
- [ ] **Fase 4 — pesquisa e fornecedores:** APIs e adaptadores para voos e alojamentos.
- [ ] **Fase 5 — inteligência:** Recommendation Engine e Price Intelligence.
- [ ] **Fase 6 — experiência de utilização:** interface web e planeador inicial.
- [ ] **Fase 7 — qualidade e operação:** testes, CI/CD, observabilidade e preparação para produção.
- [ ] **Fase futura — transações:** reservas e pagamentos.

## Estado de execução

As Fases 1 e 2 estão concluídas. O repositório está preparado para iniciar a Fase 3: criação da estrutura executável do monorepo e do ambiente Docker. Até essa implementação estar concluída e validada, não devem ser considerados disponíveis comandos de arranque, serviços de aplicação ou integrações.
