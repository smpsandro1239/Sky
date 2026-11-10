# SKY — Intelligent Travel Platform

**Discover better. Compare smarter. Travel further.**

O SKY é uma plataforma inteligente de descoberta, comparação e planeamento de viagens. O objetivo é ajudar cada cliente a encontrar opções de voos e alojamentos considerando preço total, qualidade, localização, conveniência, condições e preferências pessoais.

A visão de longo prazo é uma plataforma integral de viagens. O princípio central é recomendar a melhor opção para cada pessoa — não apenas a mais barata — e explicar os motivos da recomendação.

## Estado do projeto

**Fases 1 e 2 concluídas. Fase 3 em implementação.** A base técnica inclui Docker Compose, PostgreSQL, Redis, API FastAPI, autenticação JWT, migrações Alembic e frontend Next.js.

| Área | Estado |
|---|---|
| Fase 1 — visão e âmbito do produto | Concluída |
| Fase 2 — arquitetura e documentação | Concluída |
| Docker Compose, PostgreSQL e Redis | Base publicada; validação local ainda necessária |
| API FastAPI e autenticação | Registo, login, perfil e JWT implementados |
| Gestão de viagens | CRUD implementado e testado na API |
| Voos e alojamentos | CRUD completo associado a viagens; testes API aprovados na CI |
| Frontend — landing page | Publicada |
| Frontend — registo e login | Implementados com sessão em cookie HttpOnly |
| Frontend — dashboard | Perfil, listagem, criação e eliminação de viagens integrados com a API |
| CI GitHub Actions | Execuções recentes aprovadas na base API; validação das últimas alterações frontend em curso |
| Pesquisa externa, recomendações e favoritos | Por implementar |
| Reservas e pagamentos | Fase futura |

As páginas de autenticação e dashboard estão implementadas no código, mas ainda precisam de validação funcional em Docker e testes de ponta a ponta. Não existe ainda pesquisa real de inventário nem ligação a fornecedores externos.

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

A arquitetura será preparada para esta evolução, mas reservas e pagamentos não fazem parte da entrega atual. O SKY não armazenará dados completos de cartões; os pagamentos serão delegados a prestadores especializados.

## Arquitetura tecnológica

| Camada | Tecnologia |
|---|---|
| Web | Next.js, React, TypeScript |
| UI e estilos | CSS modular global; sistema de design em evolução |
| API | Python, FastAPI, Pydantic |
| Persistência | PostgreSQL, SQLAlchemy e Alembic |
| Cache | Redis |
| Ambiente | Docker, Docker Compose |
| Testes | Pytest, HTTPX; testes frontend e E2E por acrescentar |
| CI/CD | GitHub Actions |

A arquitetura inicial é um **monólito modular**, evitando microserviços prematuros. O frontend usa rotas Next.js do lado do servidor como BFF para encaminhar pedidos autenticados à API. O token JWT é guardado num cookie HttpOnly, não acessível a JavaScript no browser.

## Estrutura do monorepo

```text
sky/
├── apps/
│   ├── web/                 # Next.js — landing, auth e dashboard
│   └── api/                 # FastAPI — domínio e API
├── packages/                # bibliotecas partilhadas (fases seguintes)
├── infrastructure/          # infraestrutura adicional (fases seguintes)
├── docs/                    # documentação técnica
├── .github/workflows/       # CI
├── compose.yaml
├── .env.example
└── README.md
```

## Executar localmente

Requisitos: Docker Desktop com Docker Compose e Git.

1. Clonar o repositório:
   ```powershell
   git clone https://github.com/smpsandro1239/Sky.git
   cd Sky
   ```
2. Criar o ficheiro de ambiente:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Construir e iniciar:
   ```powershell
   docker compose up --build -d
   ```
4. Endereços locais:
   - Web: http://localhost:3000
   - Login: http://localhost:3000/login
   - Registo: http://localhost:3000/register
   - Dashboard: http://localhost:3000/dashboard
   - API: http://localhost:8000
   - OpenAPI: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/health

Parar: `docker compose down`. Para remover também os dados da base de dados: `docker compose down -v` (ação destrutiva).

**Nota:** a criação de conta, login e gestão básica de viagens (listar, criar, editar e eliminar) estão implementados no dashboard. A validação funcional ponta a ponta em Docker/browser, a pesquisa real de voos/hotéis e as reservas ainda não estão disponíveis.

## Documentação

- [Arquitetura do sistema](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Arquitetura frontend](docs/architecture/FRONTEND.md)
- [Arquitetura backend](docs/architecture/BACKEND.md)
- [Modelo de dados](docs/database/DATABASE.md)
- [Contrato da API](docs/api/API.md)
- [Segurança](docs/security/SECURITY.md)
- [Decisões técnicas](docs/decisions/)
- [SKY Design System](docs/design/SKY_DESIGN_SYSTEM.md)

## Princípios do projeto

1. Recomendações explicáveis e comparações transparentes.
2. Preço total, condições e qualidade — não apenas preço anunciado.
3. APIs oficiais e fornecedores autorizados; evitar dependência de scraping.
4. Separação entre domínio de negócio e fornecedores externos.
5. Privacidade, segurança, acessibilidade e testes desde o início.
6. Distinguir sempre funcionalidades implementadas, validadas e planeadas.

## Roadmap técnico

- [x] **Fase 1 — descoberta e definição do produto.**
- [x] **Fase 2 — arquitetura e documentação.**
- [ ] **Fase 3 — fundações:** Docker, API, autenticação, CRUD de viagens, voos e alojamentos; frontend com registo, login, dashboard e criação/eliminação de viagens. Falta validação funcional Docker/E2E.
- [ ] **Fase 4 — gestão frontend:** edição de viagens integrada no dashboard; gestão frontend de voos e alojamentos ainda por implementar.
- [ ] **Fase 5 — pesquisa e fornecedores:** APIs oficiais e adaptadores para voos e alojamentos.
- [ ] **Fase 6 — inteligência:** Recommendation Engine e Price Intelligence.
- [ ] **Fase 7 — qualidade e operação:** testes E2E, CI/CD, observabilidade e preparação para produção.
- [ ] **Fase futura — transações:** reservas e pagamentos.
