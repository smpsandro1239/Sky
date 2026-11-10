# SKY — Intelligent Travel Platform

**Discover better. Compare smarter. Travel further.**

O SKY é uma plataforma inteligente de descoberta, comparação e planeamento de viagens. O objetivo é ajudar cada cliente a encontrar as melhores opções de voos e alojamentos, considerando preço total, qualidade, localização, conveniência, condições e preferências pessoais.

A visão de longo prazo é uma plataforma integral de viagens, incluindo descoberta, comparação, planeamento, reservas, pagamentos e acompanhamento pós-compra. O princípio central é recomendar a melhor opção para cada pessoa — não apenas a mais barata — e explicar os motivos da recomendação.

## Estado do projeto

**Estado atual: documentação e arquitetura inicial.** A aplicação ainda não está implementada. Os serviços Docker, APIs, integrações e interfaces descritos neste repositório são planeados, não funcionalidades disponíveis.

| Área | Estado |
|---|---|
| Visão e âmbito do produto | Definidos |
| Direção visual SKY Design System | Aprovada |
| Arquitetura técnica | Proposta |
| Documentação inicial | Em construção |
| Frontend e backend | Por implementar |
| Base de dados e Docker | Por implementar |
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

1. Concluir documentação e decisões arquiteturais.
2. Criar monorepo, Docker Compose e configuração local.
3. Implementar fundações do backend, frontend e persistência.
4. Implementar pesquisa e adaptadores de fornecedores.
5. Desenvolver Recommendation Engine e Price Intelligence.
6. Construir a experiência web e o planeador inicial.
7. Adicionar testes, CI/CD, observabilidade e preparação para produção.
8. Desenvolver reservas e pagamentos numa fase posterior.

## Estado de execução

Este repositório encontra-se na fase de documentação. Ainda não existem instruções de arranque Docker funcionais nem serviços de aplicação implementados. Esses comandos serão acrescentados e testados quando os respetivos ficheiros forem criados.
