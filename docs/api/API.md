# API SKY — Contrato inicial

## Estado

A API FastAPI está implementada parcialmente. Existem endpoints de saúde, autenticação, gestão de viagens e associação de voos/alojamentos a viagens. Pesquisa externa, favoritos, recomendações e alertas continuam por implementar. Os testes automatizados estão publicados; a execução integral em CI e no ambiente Docker deve ser confirmada.

## Base path

`/api/v1`

Formato: JSON. A aplicação disponibiliza documentação OpenAPI em `/docs` e ReDoc em `/redoc`.

## Endpoints implementados

| Método | Caminho | Autenticação | Objetivo |
|---|---|---|---|
| GET | `/health` | Não | Verificação de saúde |
| POST | `/auth/register` | Não | Criar conta |
| POST | `/auth/login` | Não | Obter token de acesso |
| GET | `/auth/me` | Bearer | Consultar perfil autenticado |
| GET | `/trips` | Bearer | Listar as viagens do utilizador |
| POST | `/trips` | Bearer | Criar viagem |
| GET | `/trips/{trip_id}` | Bearer | Consultar uma viagem própria |
| PATCH | `/trips/{trip_id}` | Bearer | Atualizar uma viagem própria |
| DELETE | `/trips/{trip_id}` | Bearer | Eliminar uma viagem própria |
| GET | `/trips/{trip_id}/flights` | Bearer | Listar voos associados à viagem |
| POST | `/trips/{trip_id}/flights` | Bearer | Associar um voo à viagem |
| GET | `/trips/{trip_id}/accommodations` | Bearer | Listar alojamentos associados à viagem |
| POST | `/trips/{trip_id}/accommodations` | Bearer | Associar um alojamento à viagem |

### Autenticação

O login devolve um access token JWT. Nos endpoints privados, enviar:

```http
Authorization: Bearer <access_token>
```

A API valida o token e confirma que a conta existe e está ativa. Os recursos de viagem, voos e alojamentos são sempre acedidos através de uma viagem pertencente ao utilizador autenticado. Uma viagem pertencente a outra conta é apresentada como não encontrada (404).

### Criar uma viagem

Exemplo de pedido:

```json
{
  "name": "Férias de verão",
  "destination": "Madeira",
  "start_date": "2027-08-01",
  "end_date": "2027-08-10",
  "notes": "Viagem em família"
}
```

`name` e `destination` são obrigatórios. As datas e as notas são opcionais. Quando ambas as datas são fornecidas, a data final não pode ser anterior à data inicial.

### Associar um voo

Exemplo de pedido para `POST /trips/{trip_id}/flights`:

```json
{
  "provider": "Companhia aérea",
  "origin": "OPO",
  "destination": "FNC",
  "departure_at": "2027-08-01T08:00:00Z",
  "arrival_at": "2027-08-01T10:00:00Z",
  "price_amount": "89.90",
  "price_currency": "EUR"
}
```

Os códigos de aeroporto são normalizados para maiúsculas e têm de conter três letras. A origem e o destino têm de ser diferentes. Quando indicada, a chegada tem de ser posterior à partida. O preço é opcional e, quando fornecido, tem de ser positivo.

### Associar um alojamento

Exemplo de pedido para `POST /trips/{trip_id}/accommodations`:

```json
{
  "provider": "Fornecedor",
  "name": "Hotel Central",
  "location": "Funchal",
  "check_in": "2027-08-01",
  "check_out": "2027-08-05",
  "price_amount": "420.00",
  "price_currency": "EUR"
}
```

A data de saída tem de ser posterior à data de entrada. O preço é opcional e, quando fornecido, tem de ser positivo.

### Códigos HTTP usados

- `201`: recurso criado.
- `200`: pedido concluído.
- `204`: recurso eliminado.
- `401`: autenticação em falta ou inválida.
- `404`: viagem inexistente ou não pertencente ao utilizador.
- `422`: payload inválido.
- `409`: conflito no registo de conta.

## Endpoints planeados

| Método | Caminho | Objetivo |
|---|---|---|
| POST | `/search/flights` | Pesquisar voos em fornecedores externos |
| POST | `/search/hotels` | Pesquisar alojamento em fornecedores externos |
| GET | `/offers/{offer_id}` | Consultar oferta normalizada |
| POST | `/recommendations` | Calcular recomendações |
| GET | `/favorites` | Listar favoritos |
| POST | `/favorites` | Guardar favorito |
| DELETE | `/favorites/{favorite_id}` | Remover favorito |
| POST | `/price-alerts` | Criar alerta de preço |

Os endpoints de voos e alojamentos acima descritos apenas permitem registar e consultar elementos associados a uma viagem. Não pesquisam inventário em tempo real nem representam reservas confirmadas.

## Pesquisa — requisitos de validação

Os futuros pedidos de pesquisa deverão validar:
- Origem/destino ou localização.
- Datas e flexibilidade.
- Número e composição dos viajantes.
- Moeda e região, quando aplicável.
- Preferências e filtros.
- Limites de paginação.

Não aceitar valores arbitrários sem validação nem confiar em preços calculados pelo cliente.

## Segurança e operação

- Autenticação e autorização nos recursos privados.
- Rate limiting por utilizador/IP conforme risco.
- Timeouts para fornecedores.
- Validação de payloads.
- CORS restritivo por ambiente.
- Registos com request ID.
- Paginação e limites máximos.
- Idempotência nos comandos que possam criar operações financeiras ou reservas no futuro.

## Compatibilidade

Mudanças incompatíveis devem exigir nova versão ou política explícita de descontinuação. A API deve documentar unidades, moedas, fusos horários, campos opcionais e semântica de disponibilidade.
