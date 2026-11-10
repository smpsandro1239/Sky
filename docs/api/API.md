# API SKY — Convenções e Contrato Inicial

## Estado

Este documento define convenções e endpoints planeados. A API ainda não está implementada; os exemplos não devem ser interpretados como endpoints operacionais.

## Base path

`/api/v1`

Formato principal: JSON. A documentação OpenAPI será gerada pela aplicação FastAPI.

## Recursos planeados

| Método | Caminho | Objetivo |
|---|---|---|
| GET | `/health` | Verificação de saúde |
| POST | `/search/flights` | Pesquisar voos |
| POST | `/search/hotels` | Pesquisar alojamento |
| GET | `/offers/{offer_id}` | Consultar oferta normalizada |
| POST | `/recommendations` | Calcular recomendações |
| GET | `/favorites` | Listar favoritos |
| POST | `/favorites` | Guardar favorito |
| DELETE | `/favorites/{favorite_id}` | Remover favorito |
| GET | `/trips` | Listar viagens |
| POST | `/trips` | Criar viagem |
| POST | `/price-alerts` | Criar alerta de preço |

Os caminhos poderão evoluir durante o desenho dos contratos e não estão publicados como serviço.

## Pesquisa

Os pedidos de pesquisa deverão validar:
- Origem/destino ou localização.
- Datas e flexibilidade.
- Número e composição dos viajantes.
- Moeda e região, quando aplicável.
- Preferências e filtros.
- Limites de paginação.

Não aceitar valores arbitrários sem validação nem confiar em preços calculados pelo cliente.

## Formato de resposta conceptual

```json
{
  "data": [],
  "meta": {
    "request_id": "uuid",
    "generated_at": "2026-01-01T12:00:00Z"
  }
}
```

## Erros

Formato conceptual:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Os critérios de pesquisa são inválidos.",
    "request_id": "uuid"
  }
}
```

Não devolver stack traces, segredos ou detalhes internos ao cliente.

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
