# Arquitetura Backend SKY

## Objetivos

Disponibilizar uma API segura e versionada para pesquisa, comparação, recomendações, favoritos, alertas e planeamento de viagens.

## Stack proposta

- Python e FastAPI.
- Pydantic para validação e serialização.
- SQLAlchemy para persistência.
- PostgreSQL como base de dados principal.
- Redis para cache e coordenação auxiliar.
- Pytest e HTTPX para testes.

As versões e a estratégia de migrações serão fixadas durante a criação do projeto.

## Estrutura proposta

```text
apps/api/
├── app/
│   ├── main.py
│   ├── core/
│   ├── api/
│   │   └── v1/
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── search/
│   │   ├── flights/
│   │   ├── hotels/
│   │   ├── providers/
│   │   ├── recommendations/
│   │   ├── prices/
│   │   ├── favorites/
│   │   ├── alerts/
│   │   ├── notifications/
│   │   └── trip_planner/
│   ├── infrastructure/
│   └── tests/
└── migrations/
```

## Regras de dependência

- Routers/API tratam HTTP e delegam para serviços.
- Serviços coordenam casos de uso.
- Domínio contém regras e modelos independentes de fornecedores.
- Repositórios encapsulam acesso à persistência.
- Adaptadores integram APIs externas.
- Não colocar lógica de negócio em routers nem lógica de fornecedor no domínio.

## Convenções da API

- Prefixo versionado: `/api/v1`.
- JSON como formato principal.
- Validação de entrada e saída.
- Erros consistentes com código, mensagem e identificador de pedido.
- Paginação para coleções.
- Timeouts e limites para chamadas externas.
- Documentação OpenAPI gerada e revista.

## Fornecedores externos

Cada integração implementa uma interface interna comum e converte os dados externos para modelos canónicos SKY. Devem existir testes com respostas simuladas e tratamento de indisponibilidade, timeouts, limites e dados incompletos.

## Tarefas assíncronas

Alertas, notificações e recolha periódica de preços poderão exigir workers. A tecnologia de filas ainda será escolhida. Não introduzir uma infraestrutura adicional até existir um caso de uso concreto e critérios operacionais.

## Reservas futuras

O módulo de reservas deverá prever:
- Máquina de estados explícita.
- Chaves de idempotência.
- Webhooks assinados e deduplicação de eventos.
- Auditoria de transições.
- Reconciliação entre SKY, fornecedor e prestador de pagamentos.
- Separação entre reserva, pagamento e liquidação.

## Testes e qualidade

- Testes unitários para domínio e serviços.
- Testes de integração com PostgreSQL/Redis.
- Testes de contrato para adaptadores.
- Testes de API com HTTPX.
- Lint, type checking e análise de dependências em CI.

## Estado

Arquitetura proposta. Nenhum endpoint ou módulo backend está ainda implementado.
