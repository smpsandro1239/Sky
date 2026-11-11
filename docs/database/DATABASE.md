# Modelo de Dados SKY

## Princípios

- PostgreSQL como persistência principal.
- Identificadores internos estáveis, preferencialmente UUID.
- Timestamps em UTC.
- Valores monetários em tipo decimal, acompanhados de moeda ISO 4217.
- Integridade referencial e restrições na base de dados.
- Dados externos identificados pela origem e referência do fornecedor.
- Minimização e retenção limitada de dados pessoais.

## Entidades previstas para o MVP

As tabelas implementadas incluem `users`, `auth_identities`, `trips`, `trip_flights`, `trip_accommodations`, despesas, participantes, convites, histórico de atividade, acertos e `hotel_favorites`. Pesquisas e ofertas externas não são persistidas como reservas.

| Entidade | Responsabilidade |
|---|---|
| users | Conta e identidade interna |
| user_preferences | Preferências de viagem e pesquisa |
| search_sessions | Pesquisas efetuadas |
| search_criteria | Critérios normalizados da pesquisa |
| providers | Catálogo de fornecedores |
| flight_offers | Ofertas de voo normalizadas |
| hotel_offers | Ofertas de alojamento normalizadas |
| price_observations | Observações de preço ao longo do tempo |
| hotel_favorites | Hotéis guardados por utilizador, com unicidade por conta e referência do hotel |
| price_alerts | Regras de alerta |
| trips | Viagens planeadas |
| trip_items | Elementos de um itinerário |

## Relações conceptuais

```mermaid
erDiagram
  USERS ||--o| USER_PREFERENCES : has
  USERS ||--o{ SEARCH_SESSIONS : creates
  SEARCH_SESSIONS ||--o{ FLIGHT_OFFERS : returns
  SEARCH_SESSIONS ||--o{ HOTEL_OFFERS : returns
  PROVIDERS ||--o{ FLIGHT_OFFERS : supplies
  PROVIDERS ||--o{ HOTEL_OFFERS : supplies
  USERS ||--o{ HOTEL_FAVORITES : saves
  USERS ||--o{ PRICE_ALERTS : configures
  USERS ||--o{ TRIPS : plans
  TRIPS ||--o{ TRIP_ITEMS : contains
```

## Campos transversais recomendados

Quando aplicável:
- `id`: UUID.
- `created_at` e `updated_at`: timestamp UTC.
- `provider_id` e `provider_reference`: rastreabilidade de origem.
- `currency`: código ISO 4217.
- `observed_at` e `expires_at`: validade temporal da informação externa.

## Ofertas e preços

Uma oferta não deve ser tratada como preço garantido. O modelo deve conservar:
- Preço total conhecido e moeda.
- Componentes incluídos/excluídos, quando fornecidos.
- Condições de bagagem, cancelamento e alteração, quando disponíveis.
- Fornecedor e referência externa.
- Momento da recolha e validade/expiração.
- Estado de disponibilidade, se fornecido.

A interface deve distinguir preço observado, preço indicativo e preço confirmado pelo fornecedor.

## Reservas e pagamentos — fase futura

Entidades futuras possíveis:
- `bookings`
- `booking_items`
- `booking_status_events`
- `payment_attempts`
- `payment_webhook_events`
- `refunds`

Não armazenar números completos de cartões nem códigos de segurança. Guardar apenas referências/tokens do prestador e metadados estritamente necessários.

## Migrações e integridade

As alterações ao esquema devem ser versionadas por migrações. Evitar alterações manuais não reproduzíveis em ambientes partilhados. Definir índices com base em consultas reais e medir antes de otimizar.

## Esquema e migrações implementados

As migrações Alembic versionam o esquema relacional, incluindo contas, viagens, voos, alojamentos, despesas, participantes, convites, histórico, acertos e favoritos de hotéis. A migração `0011_hotel_favorites` cria `hotel_favorites`, ligada a `users` com eliminação em cascata e restrição única sobre `(user_id, hotel_id)`. O serviço API executa `alembic upgrade head` antes de arrancar no contentor. Os favoritos guardam apenas a referência e os dados de identificação do hotel; não guardam uma oferta, preço ou reserva.
