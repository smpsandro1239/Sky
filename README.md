# SKY — Intelligent Travel Platform

**Discover better. Compare smarter. Travel further.**

O SKY é uma plataforma inteligente de descoberta, comparação e planeamento de viagens. O objetivo é ajudar cada cliente a encontrar opções de voos e alojamentos considerando preço total, qualidade, localização, conveniência, condições e preferências pessoais.

A visão de longo prazo é uma plataforma integral de viagens. O princípio central é recomendar a melhor opção para cada pessoa — não apenas a mais barata — e explicar os motivos da recomendação.

## Estado do projeto

**Fases 1 e 2 concluídas. Fase 3 — fundações e planeamento colaborativo — implementada na API e frontend.** A validação funcional ponta a ponta em Docker/browser continua pendente. A base técnica inclui Docker Compose, PostgreSQL, Redis, API FastAPI, autenticação JWT, migrações Alembic e frontend Next.js.

| Área | Estado |
|---|---|
| Fase 1 — visão e âmbito do produto | Concluída |
| Fase 2 — arquitetura e documentação | Concluída |
| Docker Compose, PostgreSQL e Redis | Base publicada; validação local ainda necessária |
| API FastAPI e autenticação | Registo, login, perfil e JWT implementados |
| Gestão de viagens | CRUD implementado e testado na API |
| Voos e alojamentos | CRUD completo associado a viagens; testes API aprovados na CI |
| Orçamento por viagem | Limite configurável, moeda, custos de voos/alojamentos e saldo calculado |
| Despesas por viagem | Registo, edição, eliminação, categorias e integração dos valores no resumo financeiro; testes API e migrações aprovados |
| Participantes por viagem | Gestão de participantes por viagem, com isolamento por proprietário |
| Divisão de despesas e acerto de contas | Registo do pagador, partilhas por participante, cálculo de saldos por moeda, sugestões de transferências e registo de pagamentos efetuados |
| Convites e permissões de viagem | Convites com token aleatório, hash persistido e expiração de 7 dias; papéis de proprietário, editor e leitor aplicados na API; proprietário pode alterar permissões de membros; envio SMTP opcional configurável por variáveis de ambiente; sem SMTP, o link continua disponível para partilha manual |
| Frontend — convites e partilha | Escolha de papel no convite, cópia de link, revogação, aceitação autenticada, dashboard com viagens partilhadas e modo de leitura |
| Frontend — landing page | Publicada |
| Frontend — registo e login | Implementados com sessão em cookie HttpOnly |
| Frontend — dashboard | Perfil, listagem, criação, edição e eliminação de viagens integrados com a API |
| Frontend — planeador de viagem | Página de detalhe com CRUD de voos, alojamentos e despesas via BFF; orçamento e saldo por moeda |
| CI GitHub Actions | Pipeline configurado para testes API, validação de migrações, ESLint e TypeScript; consultar a execução mais recente no GitHub Actions |
| Pesquisa externa de voos | Adaptador Amadeus sandbox na API, endpoint autenticado, normalização de ofertas e formulário integrado; requer credenciais e validação CI/E2E |
| Recommendation Engine — voos | Ranking explicável relativo aos resultados da pesquisa: preço (50%), duração (30%) e escalas (20%); score e motivos apresentados na interface; testes unitários adicionados; falta validação CI/E2E e evolução das preferências do utilizador |
| Hotel Intelligence — alojamentos | Ranking explicável por preço/noite (70%) e condições de cancelamento explicitamente reconhecidas (30%); preço/noite, noites, score e motivos apresentados na interface; testes unitários adicionados; falta validação CI/E2E |
| Pesquisa externa de alojamentos e favoritos | Adaptador Amadeus sandbox, endpoint autenticado, pesquisa integrada, favoritos e comparação de até três ofertas; requer credenciais e validação CI/E2E |
| Recommendation Engine — hotéis | Ranking explicável, preço médio por noite e condições de cancelamento; testes unitários adicionados; falta validação CI/E2E |
| Reservas e pagamentos | Fase futura |

As páginas de autenticação e dashboard estão implementadas no código, mas ainda precisam de validação funcional em Docker e testes de ponta a ponta. A pesquisa de voos Amadeus já tem um adaptador no backend e um formulário integrado na página de detalhe da viagem. A consulta real depende de credenciais sandbox configuradas no servidor; a interface apresenta ofertas, segmentos, escalas e preços, mas ainda não reserva nem emite bilhetes. Os convites podem ser criados e aceites por link; o envio por email está disponível quando o SMTP é configurado através das variáveis `SMTP_*` no ficheiro `.env.example`. Sem SMTP, o link pode ser partilhado manualmente.

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

**Nota:** o dashboard permite gerir viagens, voos, alojamentos e despesas, incluindo partilhas, balanços e acesso colaborativo por proprietário/editor/leitor. As operações usam a API através do BFF autenticado. A última execução de CI anteriormente confirmada concluiu com sucesso os testes API, migrações, ESLint e TypeScript; os novos commits de pesquisa de voos aguardam confirmação da respetiva execução. A validação funcional ponta a ponta em Docker/browser ainda não está confirmada. A pesquisa de voos tem um adaptador Amadeus no backend e interface integrada no detalhe da viagem; depende de credenciais sandbox e a validação ponta a ponta continua pendente. A pesquisa de alojamentos, reservas e pagamentos não estão implementadas. O envio de convites por email requer configuração SMTP.

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
- [x] **Fase 3 — fundações:** Docker, API, autenticação, CRUD de viagens/voos/alojamentos/despesas, orçamento, participantes, convites e permissões colaborativas. Falta validação funcional Docker/E2E.
- [x] **Fase 4 — gestão frontend (primeira entrega):** gestão de viagens, voos, alojamentos, despesas, orçamento, participantes, convites e balanços integrada no dashboard/planeador através do BFF. Falta validação E2E e refinamento de UX.
- [ ] **Fase 5 — pesquisa e fornecedores:** adaptador inicial Amadeus para pesquisa de voos publicado; falta validar CI, configurar credenciais sandbox e integrar pesquisa no frontend. Pesquisa de alojamentos e respetivo fornecedor continuam por implementar.
- [ ] **Fase 6 — inteligência:** primeira versão do ranking explicável de voos publicada; falta personalização por preferências, recomendação de alojamentos e Price Intelligence.
- [ ] **Fase 7 — qualidade e operação:** testes E2E, CI/CD, observabilidade e preparação para produção.
- [ ] **Fase futura — transações:** reservas e pagamentos.
