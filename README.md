# SKY — Intelligent Travel Platform

**Discover better. Compare smarter. Travel further.**

O SKY é uma plataforma inteligente de descoberta, comparação e planeamento de viagens. O objetivo é ajudar cada cliente a encontrar as melhores opções de voos e alojamentos, considerando preço total, qualidade, localização, conveniência, condições e preferências pessoais.

A visão de longo prazo é uma plataforma integral de viagens, incluindo descoberta, comparação, planeamento, reservas, pagamentos e acompanhamento pós-compra. O princípio central é recomendar a melhor opção para cada pessoa — não apenas a mais barata — e explicar os motivos da recomendação.

## Estado do projeto

**Fases 1 e 2 concluídas. Fase 3 em implementação.** A fundação inicial já inclui configuração Docker Compose, serviços PostgreSQL e Redis, uma API FastAPI com endpoint de saúde e testes, e uma interface Next.js inicial. A execução local e a integração contínua ainda precisam de ser validadas.

| Área | Estado |
|---|---|
| Fase 1 — visão e âmbito do produto | Concluída |
| Fase 2 — arquitetura, documentação e SKY Design System | Concluída |
| Docker Compose, PostgreSQL e Redis | Implementação inicial publicada |
| API FastAPI e endpoint de saúde | Implementação inicial publicada; testes por executar |
| Frontend Next.js | Estrutura e landing page iniciais publicadas |
| CI GitHub Actions | Configuração inicial publicada |
| Pesquisa real de voos e alojamentos | Por implementar |
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

## Arquitetura tecnológica

| Camada | Tecnologia |
|---|---|
| Web | Next.js, React, TypeScript |
| UI e estilos | Tailwind CSS, shadcn/ui (integração planeada) |
| API | Python, FastAPI, Pydantic |
| Persistência | PostgreSQL (infraestrutura inicial; modelo por implementar) |
| Cache | Redis (infraestrutura inicial) |
| Ambiente | Docker, Docker Compose |
| Testes | Pytest, HTTPX; testes frontend e E2E em fases posteriores |
| CI/CD | GitHub Actions |

A arquitetura inicial será um **monólito modular**, evitando microserviços prematuros. As versões e dependências serão consolidadas através dos ficheiros de configuração e validadas na primeira execução local e CI.

## Estrutura do monorepo

```text
sky/
├── apps/
│   ├── web/                 # Next.js
│   └── api/                 # FastAPI
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

1. Clonar o repositório e entrar na pasta:
   ```powershell
   git clone https://github.com/smpsandro1239/Sky.git
   cd Sky
   ```
2. Criar o ficheiro de ambiente:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Construir e iniciar os serviços:
   ```powershell
   docker compose up --build -d
   ```
4. Consultar os serviços:
   - Web: http://localhost:3000
   - API: http://localhost:8000
   - Documentação API: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/health

Parar os serviços: `docker compose down`. Para remover também os dados locais da base de dados: `docker compose down -v` (ação destrutiva).

> Nota: os campos da página inicial ainda são demonstrativos e estão desativados. Não existe ainda pesquisa real, ligação a fornecedores, autenticação ou fluxo de reserva.

## Documentação

- [Arquitetura do sistema](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Arquitetura frontend](docs/architecture/FRONTEND.md)
- [Arquitetura backend](docs/architecture/BACKEND.md)
- [Modelo de dados](docs/database/DATABASE.md)
- [Contrato e convenções da API](docs/api/API.md)
- [Segurança](docs/security/SECURITY.md)
- [Decisões técnicas](docs/decisions/)
- [SKY Design System](docs/design/SKY_DESIGN_SYSTEM.md)

## Princípios do projeto

1. Recomendações explicáveis e comparações transparentes.
2. Preço total, condições e qualidade — não apenas preço anunciado.
3. APIs oficiais e fornecedores autorizados; evitar dependência de scraping.
4. Separação entre domínio de negócio e fornecedores externos.
5. Privacidade, segurança, acessibilidade e testes desde o início.
6. Distinguir sempre funcionalidades planeadas das implementadas.

## Roadmap técnico

- [x] **Fase 1 — descoberta e definição do produto.**
- [x] **Fase 2 — arquitetura e documentação.**
- [ ] **Fase 3 — fundações do projeto:** estrutura inicial, Docker, API, frontend e CI; falta validação local e estabilização.
- [ ] **Fase 4 — pesquisa e fornecedores:** APIs e adaptadores para voos e alojamentos.
- [ ] **Fase 5 — inteligência:** Recommendation Engine e Price Intelligence.
- [ ] **Fase 6 — experiência de utilização:** interface web e planeador inicial.
- [ ] **Fase 7 — qualidade e operação:** testes, CI/CD, observabilidade e preparação para produção.
- [ ] **Fase futura — transações:** reservas e pagamentos.
