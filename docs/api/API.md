# API SKY — Contrato inicial

## Estado

A API FastAPI disponibiliza saúde, autenticação, gestão de viagens, voos, alojamentos, despesas, participantes, partilhas e balanços de despesas. Pesquisa externa, favoritos, recomendações e alertas continuam por implementar. A execução da CI e dos testes deve ser consultada no GitHub Actions.

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
| GET | `/trips/{trip_id}` | Bearer | Consultar uma viagem própria ou partilhada, incluindo o papel do utilizador |
| GET | `/trips/{trip_id}/access` | Bearer | Consultar o papel do utilizador na viagem (owner, editor ou viewer) |
| PATCH | `/trips/{trip_id}` | Bearer | Atualizar uma viagem própria |
| DELETE | `/trips/{trip_id}` | Bearer | Eliminar uma viagem própria |
| GET | `/trips/{trip_id}/flights` | Bearer | Listar voos associados à viagem |
| POST | `/trips/{trip_id}/flights` | Bearer | Associar um voo à viagem |
| PATCH | `/trips/{trip_id}/flights/{flight_id}` | Bearer | Atualizar um voo |
| DELETE | `/trips/{trip_id}/flights/{flight_id}` | Bearer | Eliminar um voo |
| GET | `/trips/{trip_id}/accommodations` | Bearer | Listar alojamentos associados |
| POST | `/trips/{trip_id}/accommodations` | Bearer | Associar um alojamento |
| PATCH | `/trips/{trip_id}/accommodations/{accommodation_id}` | Bearer | Atualizar um alojamento |
| DELETE | `/trips/{trip_id}/accommodations/{accommodation_id}` | Bearer | Eliminar um alojamento |
| GET | `/trips/{trip_id}/expenses` | Bearer | Listar despesas da viagem |
| POST | `/trips/{trip_id}/expenses` | Bearer | Registar despesa |
| PATCH | `/trips/{trip_id}/expenses/{expense_id}` | Bearer | Atualizar despesa; rejeita alterações que invalidem partilhas existentes |
| DELETE | `/trips/{trip_id}/expenses/{expense_id}` | Bearer | Eliminar despesa e respetivas partilhas |
| GET | `/trips/{trip_id}/participants` | Bearer | Listar participantes da viagem |
| PATCH | `/trips/{trip_id}/participants/{participant_id}` | Bearer (proprietário) | Alterar papel entre `editor` e `viewer` e atualizar convite pendente correspondente |
| POST | `/trips/{trip_id}/participants` | Bearer | Adicionar participante |
| DELETE | `/trips/{trip_id}/participants/{participant_id}` | Bearer | Remover participante sem partilhas ou despesas pagas associadas |
| POST | `/trips/{trip_id}/invitations` | Bearer | Criar convite para um endereço de email |
| GET | `/trips/{trip_id}/invitations` | Bearer | Listar convites da viagem (sem expor tokens) |
| DELETE | `/trips/{trip_id}/invitations/{invitation_id}` | Bearer | Revogar convite pendente |
| POST | `/invitations/accept` | Bearer | Aceitar convite com token e conta de email correspondente |
| GET | `/trips/{trip_id}/expenses/{expense_id}/shares` | Bearer | Consultar divisão da despesa |
| GET | `/trips/{trip_id}/balances` | Bearer | Calcular saldos e transferências sugeridas por moeda |
| PATCH | `/trips/{trip_id}/expenses/{expense_id}/shares` | Bearer | Substituir a divisão da despesa (lista de partes); lista vazia limpa a divisão |

### Autenticação e autorização

O login devolve um access token JWT. Nos endpoints privados, enviar:

```http
Authorization: Bearer <access_token>
```

A API valida o token e confirma que a conta existe e está ativa. As viagens podem ser partilhadas com contas registadas. O proprietário tem controlo total; editores podem consultar e alterar voos, alojamentos, despesas, partilhas e balanços; leitores só podem consultar. Apenas o proprietário pode alterar os metadados e orçamento da viagem, gerir participantes, alterar os seus papéis e gerir convites. A API valida o papel em cada operação; viagens não partilhadas continuam ocultas (404) e tentativas de escrita por leitores devolvem 403.

### Convites para participantes

O proprietário da viagem pode criar um convite através de `POST /trips/{trip_id}/invitations`:

```json
{ "email": "pessoa@example.com", "role": "viewer" }
```

O campo `role` aceita `viewer` (predefinição) ou `editor`. A resposta inclui `invitation_token` uma única vez e `email_sent`, que indica se o envio SMTP foi concluído. Sem `SMTP_HOST` e `SMTP_FROM_EMAIL`, o convite é criado normalmente e o link deve ser partilhado manualmente. O token é gerado aleatoriamente, só o respetivo hash SHA-256 é guardado na base de dados e o convite expira ao fim de 7 dias. A listagem nunca devolve o token. O link de aceitação deve ser partilhado apenas com o destinatário.

A pessoa convidada tem de iniciar sessão com o mesmo endereço de email e enviar `POST /invitations/accept`:

```json
{ "token": "TOKEN_RECEBIDO_NO_LINK" }
```

A aceitação associa a conta ao participante existente com o mesmo email ou cria um participante novo. Os tokens são de utilização única. Convites pendentes podem ser revogados pelo proprietário. Convites expirados, revogados ou já aceites não podem ser reutilizados.

**Entrega de email:** o serviço SMTP é opcional. Configura `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_STARTTLS` e `SMTP_USE_SSL` no ambiente da API. `SMTP_STARTTLS` e `SMTP_USE_SSL` não podem estar ativos em simultâneo. Quando não existe configuração SMTP ou o envio falha, `email_sent` é `false` e o frontend apresenta o link para partilha manual. A aceitação associa a conta à viagem com o papel definido pelo proprietário. O papel é aplicado na API e validado em cada operação. Os papéis permitidos são `editor` e `viewer`; o proprietário é sempre o dono original da viagem e não pode ser substituído por um convite.

### Criar uma viagem

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

Pedido para `POST /trips/{trip_id}/flights`:

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

Pedido para `POST /trips/{trip_id}/accommodations`:

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

### Atualizações parciais

Os endpoints PATCH aceitam apenas os campos a alterar. A API valida o estado completo resultante antes de persistir a alteração: por exemplo, não permite que a chegada de um voo fique antes da partida nem que a saída de um alojamento fique antes da entrada. Os campos obrigatórios não podem ser anulados.

### Dividir uma despesa entre participantes

Ao criar ou atualizar uma despesa, `paid_by_participant_id` identifica opcionalmente o participante que adiantou o valor. O identificador tem de pertencer à viagem. O pedido `PATCH /trips/{trip_id}/expenses/{expense_id}/shares` recebe uma lista completa de partes. Cada participante só pode surgir uma vez, tem de pertencer à viagem e cada valor tem de ser positivo. A soma é comparada ao total da despesa em cêntimos; diferenças de um cêntimo são rejeitadas. Enviar `[]` remove todas as partes. Um participante que seja pagador ou tenha partilhas associadas não pode ser eliminado (409).

O endpoint `GET /trips/{trip_id}/balances` calcula, para cada moeda, o total pago, a parte atribuída e o saldo líquido de cada participante. Inclui sugestões de transferências entre devedores e credores para liquidar os saldos com o menor número de movimentos gerado pelo algoritmo guloso. Só entram no cálculo despesas com pagador identificado e divisão guardada; despesas sem pagador ou sem partilhas ficam de fora.

Exemplo:

```json
[
  { "participant_id": "UUID-DO-PARTICIPANTE-1", "amount": "12.50" },
  { "participant_id": "UUID-DO-PARTICIPANTE-2", "amount": "12.50" }
]
```

### Códigos HTTP

- `201`: recurso criado.
- `200`: pedido concluído.
- `204`: recurso eliminado.
- `401`: autenticação em falta ou inválida.
- `404`: viagem/recurso inexistente ou sem acesso.
- `422`: payload inválido ou combinação de campos inconsistente.
- `409`: conflito de estado, por exemplo remoção de participante ligado a despesas ou alteração de despesa que invalidaria a divisão.

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

Os endpoints de voos e alojamentos implementados apenas gerem elementos associados a uma viagem. Não pesquisam inventário em tempo real nem representam reservas confirmadas.

## Pesquisa — requisitos de validação

Os futuros pedidos de pesquisa deverão validar origem/destino ou localização, datas e flexibilidade, composição dos viajantes, moeda, preferências, filtros e limites de paginação. Não confiar em preços calculados pelo cliente.

## Segurança e operação

- Autenticação e autorização nos recursos privados.
- Rate limiting por utilizador/IP conforme risco.
- Timeouts para fornecedores externos.
- Validação de payloads e limites de paginação.
- CORS restritivo por ambiente.
- Registos com request ID.
- Idempotência em operações futuras que possam criar reservas ou pagamentos.

## Compatibilidade

Mudanças incompatíveis devem exigir nova versão ou política explícita de descontinuação. A API deve documentar unidades, moedas, fusos horários, campos opcionais e semântica de disponibilidade.
