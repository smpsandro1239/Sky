# API SKY — Contrato inicial

## Estado

A API FastAPI disponibiliza saúde, autenticação, gestão de viagens, voos, alojamentos, despesas, participantes, partilhas e balanços de despesas. A pesquisa externa de voos e alojamentos tem adaptadores Amadeus em modo sandbox, condicionados à configuração de credenciais. Os favoritos de hotéis são privados por utilizador. Os endpoints de pesquisa de voos e alojamentos já aplicam ranking explicável; personalização por preferências continua por implementar; os alertas de preço têm uma primeira versão funcional na API. A execução da CI e dos testes deve ser consultada no GitHub Actions.

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
| GET | `/flights/search` | Bearer | Pesquisar ofertas externas Amadeus por rota, data, passageiros e moeda (requer credenciais) |
| GET | `/hotels/search` | Bearer | Pesquisar alojamentos e ofertas Amadeus por cidade IATA, datas, ocupação, raio e moeda (requer credenciais) |
| GET | `/hotels/favorites` | Bearer | Listar favoritos de hotéis do utilizador autenticado |
| GET | `/prices/history` | Bearer | Consultar histórico de preços observados em pesquisas de voos e alojamentos |
| GET | `/prices/alerts` | Bearer | Listar alertas de preço do utilizador autenticado |
| POST | `/prices/alerts` | Bearer | Criar alerta para uma oferta existente no histórico |
| PATCH | `/prices/alerts/{alert_id}` | Bearer | Ativar ou desativar um alerta ainda não atingido |
| DELETE | `/prices/alerts/{alert_id}` | Bearer | Eliminar um alerta próprio |
| POST | `/hotels/favorites` | Bearer | Guardar um hotel nos favoritos (operação idempotente por utilizador e hotel) |
| DELETE | `/hotels/favorites/{favorite_id}` | Bearer | Remover um favorito próprio |
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
| GET | `/trips/{trip_id}/balances` | Bearer | Calcular saldos, pagamentos já efetuados e transferências sugeridas por moeda |
| GET | `/trips/{trip_id}/settlements` | Bearer | Consultar pagamentos/acertos registados |
| POST | `/trips/{trip_id}/settlements` | Bearer (editor) | Registar um pagamento entre participantes |
| PATCH | `/trips/{trip_id}/expenses/{expense_id}/shares` | Bearer | Substituir a divisão da despesa (lista de partes); lista vazia limpa a divisão |

### Recomendações de voos e alojamentos

A pesquisa de voos devolve `duration_minutes`, `recommendation_score` e `recommendation_reasons`. O score de voos é relativo ao conjunto da mesma pesquisa: preço (50%), duração total dos itinerários (30%) e número de escalas (20%). Dimensões sem dados válidos são excluídas e os pesos disponíveis são normalizados.

A pesquisa de alojamentos devolve `nights`, `price_per_night`, `recommendation_score` e `recommendation_reasons`. O score de alojamento usa preço por noite (70%) e condições de cancelamento (30%). A dimensão de cancelamento só é considerada quando o texto do fornecedor contém uma indicação explícita reconhecida de cancelamento gratuito ou de tarifa não reembolsável. Texto ambíguo ou ausente não é interpretado como uma condição conhecida.

Ambos os scores são comparativos dentro dos resultados da mesma pesquisa, não são probabilidades, classificações absolutas de qualidade nem garantias de disponibilidade. A ordenação usa o score e critérios determinísticos de desempate.

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

O endpoint `GET /trips/{trip_id}/balances` calcula, para cada moeda, o total pago, a parte atribuída, os acertos enviados/recebidos e o saldo líquido de cada participante. Inclui sugestões de transferências entre devedores e credores para liquidar os saldos com o menor número de movimentos gerado pelo algoritmo guloso. Só entram no cálculo despesas com pagador identificado e divisão guardada; despesas sem pagador ou sem partilhas ficam de fora.

Os endpoints `GET` e `POST /trips/{trip_id}/settlements` permitem consultar e registar pagamentos reais entre participantes. O registo exige que ambos pertençam à viagem, que o pagador tenha saldo devedor e o destinatário saldo credor na moeda indicada, e que o montante não exceda o valor em aberto de qualquer um dos lados. O pagamento é refletido no saldo líquido e no histórico de atividade. Apenas proprietários e editores podem registar pagamentos; qualquer participante com acesso pode consultar o histórico de acertos.

Exemplo:

```json
[
  { "participant_id": "UUID-DO-PARTICIPANTE-1", "amount": "12.50" },
  { "participant_id": "UUID-DO-PARTICIPANTE-2", "amount": "12.50" }
]
```

### Histórico de atividade por viagem

O histórico é consultado por qualquer utilizador com acesso à viagem (proprietário, editor ou leitor):

`GET /trips/{trip_id}/activity?limit=30&offset=0`

A resposta contém `items`, `limit`, `offset` e `has_more`. O limite predefinido é 30 e o máximo é 100. A ordenação é cronológica inversa, com desempate estável pelo identificador do evento. Cada evento expõe o nome do autor, ação, tipo e identificador da entidade, resumo e data. O registo não guarda tokens de convite, credenciais, endereços de email ou payloads integrais. Os eventos são criados na mesma transação da operação correspondente.

São registadas criações e alterações da viagem, despesas, voos, alojamentos, participantes, convites e divisões de despesas, bem como a aceitação e revogação de convites. A eliminação da própria viagem elimina também o respetivo histórico.

### Favoritos de hotéis

Os favoritos são associados à conta autenticada e não a uma viagem. O endpoint `GET /hotels/favorites` devolve apenas os favoritos do utilizador. Para guardar um hotel, enviar `POST /hotels/favorites` com o identificador estável do hotel devolvido pelo Amadeus, o nome, a localização e o fornecedor:

```json
{ "provider": "amadeus", "hotel_id": "HOTEL_REFERENCE", "hotel_name": "Hotel Central", "location": "Lisboa, PT" }
```

Repetir o pedido para o mesmo `hotel_id` não cria duplicados: devolve o favorito existente. A remoção usa `DELETE /hotels/favorites/{favorite_id}` e só é permitida ao proprietário do favorito. A lista e as operações não representam uma reserva nem garantem preços ou disponibilidade.

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
| POST | `/price-alerts` | Criar alerta de preço |

A pesquisa Amadeus de alojamentos consulta hotéis por código de cidade IATA e depois procura ofertas para as datas e ocupação indicadas. A disponibilidade e os preços são devolvidos pelo fornecedor no momento da pesquisa, podem mudar e não constituem uma reserva. Os endpoints de alojamentos associados à viagem continuam a gerir apenas os registos guardados; não efetuam reservas.

## Pesquisa — requisitos de validação

Os futuros pedidos de pesquisa deverão validar origem/destino ou localização, datas e flexibilidade, composição dos viajantes, moeda, preferências, filtros e limites de paginação. Não confiar em preços calculados pelo cliente.


Parâmetros de pesquisa de alojamentos:

| Parâmetro | Obrigatório | Predefinição | Descrição |
|---|---|---|---|
| `city_code` | Sim | — | Código IATA de três letras da cidade, por exemplo LIS |
| `check_in` | Sim | — | Data de entrada em YYYY-MM-DD |
| `check_out` | Sim | — | Data de saída posterior à entrada; máximo de 30 noites |
| `adults` | Não | 2 | Número de adultos, entre 1 e 9 |
| `room_quantity` | Não | 1 | Número de quartos, entre 1 e 8 |
| `radius` | Não | 20 | Raio da pesquisa em quilómetros, entre 1 e 50 |
| `max_hotels` | Não | 20 | Máximo de hotéis consultados, entre 1 e 40 |
| `currency` | Não | EUR | Código de moeda de três letras |

A resposta contém ofertas normalizadas e ordenadas por preço total. A aplicação permite escolher adultos, quartos, raio e moeda. O botão de gravação cria um alojamento na viagem; não cria uma reserva no fornecedor. O identificador de oferta não é persistido como reserva e os preços podem deixar de estar disponíveis após a pesquisa. Quando devolvidos pelo Amadeus, os resultados também incluem tipo de pagamento, prazo e descrição da política de cancelamento. Estes campos são opcionais: a ausência significa que o fornecedor não os disponibilizou na resposta, não que exista cancelamento gratuito ou pagamento flexível. A comparação na interface permite selecionar até três ofertas e apresenta preço total, média por noite e os detalhes de quarto, regime e políticas efetivamente recebidos.

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


### Pesquisa externa de voos (Amadeus)

O endpoint `GET /flights/search` consulta ofertas de voo no fornecedor Amadeus. Requer autenticação Bearer e credenciais de API configuradas no ambiente da API:

- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `AMADEUS_BASE_URL` (predefinição: `https://test.api.amadeus.com`)

O endereço predefinido utiliza o ambiente de testes da Amadeus. Para produção, a conta e o acesso ao ambiente de produção têm de ser aprovados pelo fornecedor e a variável de ambiente deve ser alterada deliberadamente. Nunca colocar credenciais no frontend ou no repositório.

Parâmetros:

| Parâmetro | Obrigatório | Predefinição | Descrição |
|---|---|---|---|
| `origin` | Sim | — | Código IATA de três letras, por exemplo OPO |
| `destination` | Sim | — | Código IATA de três letras, diferente da origem |
| `departure_date` | Sim | — | Data de partida em YYYY-MM-DD |
| `return_date` | Não | — | Data de regresso posterior à partida |
| `adults` | Não | 1 | Passageiros adultos, entre 1 e 9 |
| `currency` | Não | EUR | Código de moeda de três letras |
| `non_stop` | Não | false | Limitar a voos diretos |
| `max_results` | Não | 20 | Número máximo de ofertas, entre 1 e 50 |

Exemplo:

```http
GET /api/v1/flights/search?origin=OPO&destination=LIS&departure_date=2027-08-10&adults=2&currency=EUR
Authorization: Bearer <access_token>
```

A resposta normaliza o preço total, moeda, número de escalas, duração total estimada e segmentos de cada itinerário. Cada oferta inclui `recommendation_score` (0–100) e `recommendation_reasons`. O ranking é relativo às ofertas devolvidas na mesma pesquisa: preço tem peso de 50%, duração de 30% e escalas de 20%; dimensões sem dados válidos são excluídas e os pesos restantes são normalizados. A duração soma o tempo decorrido de cada itinerário, incluindo ligações. O score não é uma probabilidade nem deve ser comparado entre pesquisas diferentes. As ofertas são ordenadas por score decrescente, seguindo-se preço, escalas e identificador para desempate. Esta integração apenas pesquisa ofertas: não reserva, não emite bilhetes e não garante disponibilidade após a resposta. A pesquisa de ida e volta utiliza a mesma quantidade de adultos para ambos os segmentos.

Sem credenciais, a API responde `503`; falhas do fornecedor são traduzidas em `502`; critérios inválidos são rejeitados com `422`. O adaptador mantém o token OAuth em memória durante a validade indicada pelo fornecedor. A cache é local ao processo da API. A interface do detalhe da viagem permite a utilizadores com permissões de edição guardar uma oferta selecionada: cada segmento do itinerário é criado através de `POST /api/v1/trips/{trip_id}/flights`. O preço total da oferta fica associado apenas ao primeiro segmento para não duplicar o custo no orçamento. Se a criação de um segmento posterior falhar, os segmentos já criados permanecem guardados e a interface informa quantos foram persistidos.

### SKY Price Intelligence — histórico de preços observados

As pesquisas autenticadas de voos e alojamentos guardam automaticamente uma observação por oferta devolvida pelo fornecedor. Cada observação contém fornecedor, identificador da oferta, nome, preço total, moeda, disponibilidade reportada, instante de recolha e critérios da pesquisa. A recolha começa após a publicação desta funcionalidade: **não existe reconstrução de histórico anterior**.

As respostas de pesquisa incluem o campo `search_key`, uma impressão digital SHA-256 determinística dos critérios normalizados. A chave não inclui o utilizador; o acesso ao histórico continua isolado pelo utilizador autenticado. Critérios equivalentes produzem a mesma chave. Os registos de cada execução são agrupados por `capture_id`, com unicidade por execução e oferta.

Consultar o histórico:

```http
GET /api/v1/prices/history?search_type=flight&search_key=<64-hex>
Authorization: Bearer <access_token>
```

Parâmetros:
- `search_type`: `flight` ou `hotel`.
- `search_key`: chave devolvida pela pesquisa correspondente.
- `item_key`: opcional; limita a uma oferta (para hotéis combina o identificador do hotel e o identificador da tarifa).
- `limit`: opcional, entre 1 e 500; predefinição 100.

A resposta apresenta observações por ordem cronológica, com `observations_count` e os valores de preço efetivamente recolhidos. O endpoint só devolve dados pertencentes ao utilizador autenticado. Se ainda não houver observações para a chave, responde `404`. Os preços não são previsões nem garantias de preço futuro; diferenças entre observações só são comparáveis quando a chave de pesquisa e a moeda coincidem.



### Alertas de preço

Os alertas são privados por utilizador e só podem ser criados para uma oferta disponível já observada pelo mesmo utilizador. O pedido `POST /prices/alerts` recebe `search_type`, `search_key`, `item_key`, `item_name`, `currency` e `target_price`. O preço-alvo tem de ser positivo. A API compara apenas observações da mesma pesquisa, oferta e moeda. A identidade da oferta é calculada por fingerprint SHA-256 estável: voos usam itinerários, horários e detalhes tarifários; hotéis usam hotel, quarto e condições tarifárias. O ID efémero da oferta Amadeus deixa de ser usado para associar recolhas. Quando uma nova pesquisa do fornecedor regista um preço igual ou inferior ao objetivo, o alerta passa para inativo e guarda `triggered_price` e `triggered_at`. `GET /prices/alerts` devolve o estado; `PATCH` permite desativar ou reativar alertas ainda não atingidos e `DELETE` remove um alerta.

A avaliação pode ocorrer numa pesquisa manual ou no worker periódico `app.price_monitor_worker`, executado como serviço `price-monitor` no `compose.yaml`. O worker procura alertas activos, recupera os critérios da última observação e volta a consultar o Amadeus. Por omissão, limita cada combinação utilizador/pesquisa a uma consulta a cada 6 horas, com bloqueio distribuído Redis; em falha, tenta novamente após 10 minutos. Pesquisas de voos após a partida e estadias após a data de saída são ignoradas para evitar chamadas desnecessárias ao fornecedor. Os intervalos são configuráveis por `PRICE_MONITOR_INTERVAL_SECONDS`, `PRICE_MONITOR_POLL_SECONDS` e `PRICE_MONITOR_RETRY_SECONDS`. O worker depende de credenciais Amadeus e de Redis. Ainda não existe envio de notificações por email, push ou SMS. Criar um alerta não reserva a oferta nem garante que o preço continue disponível.

Na interface, o painel Price Intelligence permite selecionar uma oferta e visualizar o último preço, mínimo e máximo observados, número de recolhas e gráfico cronológico. Uma primeira pesquisa gera normalmente apenas o primeiro ponto; a evolução só fica visível após novas pesquisas com os mesmos critérios. A ausência de histórico é apresentada como estado vazio, não como erro. A interface usa a mesma identidade estável da API para associar observações e alertas entre pesquisas. A interface não estima preços futuros.

## Notificações

- `GET /api/v1/notifications?limit=20&offset=0&unread_only=false`: lista notificações do utilizador autenticado, devolve contagem total por ler e paginação.
- `PATCH /api/v1/notifications/{notification_id}/read`: marca uma notificação própria como lida.
- `POST /api/v1/notifications/read-all`: marca todas as notificações próprias como lidas e devolve o número actualizado.
- As notificações são privadas, persistentes e eliminadas em cascata quando a conta é eliminada.
- Quando um alerta de preço é atingido, é criada uma notificação na mesma transacção que actualiza o alerta. Se o preço já estiver no alvo no momento da criação, a notificação é criada imediatamente.
- Eventos de viagens também geram notificações internas: convite enviado a uma conta registada (`trip_invitation`), convite aceite (`trip_invitation_accepted`), alteração de permissão (`trip_role_changed`) e actualização dos dados da viagem (`trip_updated`).
- Os eventos são persistidos na mesma transacção da alteração, sempre que aplicável. Só são notificados utilizadores associados à viagem; o autor da alteração é excluído e convites para endereços sem conta SKY não criam notificações.
- A interface do dashboard apresenta o contador de notificações por ler e permite abrir, marcar uma notificação como lida ou marcar todas como lidas.
