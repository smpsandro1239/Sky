# Arquitetura Frontend SKY

## Objetivos

Criar uma experiência responsiva, rápida e acessível para descobrir destinos, pesquisar voos e alojamentos, comparar opções e organizar viagens.

## Stack implementada

- Next.js 16 com App Router.
- React 19 e TypeScript em modo estrito.
- CSS global com tokens de cor e layouts responsivos.
- Next.js Route Handlers como Backend for Frontend (BFF) para autenticação e pedidos autenticados.

Tailwind CSS e shadcn/ui continuam como opções de evolução; ainda não estão integrados.

## Rotas existentes

- `/`: landing page.
- `/login`: início de sessão.
- `/register`: criação de conta.
- `/dashboard`: perfil e listagem das viagens do utilizador.

Rotas previstas para fases seguintes:

- `/flights`: resultados de voos.
- `/hotels`: resultados de alojamento.
- `/destinations`: descoberta de destinos.
- `/trips`: viagens e planeador.
- `/favorites`: favoritos.
- `/account`: perfil e preferências.

## Autenticação e BFF

O browser envia credenciais para `/api/auth/login` e `/api/auth/register`. O Next.js encaminha o pedido para a API FastAPI através de `API_INTERNAL_URL`.

Após login bem-sucedido:
1. O BFF obtém o JWT na API.
2. O BFF consulta `/auth/me` para confirmar o perfil.
3. O JWT é guardado num cookie `HttpOnly`, `SameSite=Lax`, com `Secure` em produção e duração limitada pela expiração do token.
4. O browser não recebe o JWT no corpo da resposta nem o guarda em localStorage.
5. Os pedidos autenticados permitidos passam pelo handler `/api/backend/*`, que lê o cookie no servidor e encaminha o Bearer token para a API.

O handler backend tem uma allowlist explícita: GET em `auth/me` e `trips`, POST em `trips` e PATCH/DELETE apenas em `trips/{uuid}`. O dashboard permite listar, criar, editar e eliminar viagens. As operações frontend sobre voos/alojamentos ainda não estão expostas.

## Estado e dados

- Estado local React para formulários e carregamento.
- Camada BFF para comunicação autenticada.
- Dados de perfil e viagens carregados a partir da API.
- Tokens sensíveis não são guardados em localStorage.
- Os resultados e formulários de pesquisa ainda não estão ligados a fornecedores externos.

## Componentes de produto

Componentes de domínio previstos: `FlightCard`, `HotelCard`, `PriceBadge`, `DestinationCard`, `InteractiveMap`, `PriceChart` e `FilterSidebar`. Ainda não estão implementados como biblioteca partilhada.

## Design e acessibilidade

- Layouts adaptáveis a dispositivos móveis.
- Cores e superfícies definidas por variáveis CSS.
- Labels e mensagens de erro nos formulários.
- Foco visível nos campos.
- Objetivo de conformidade WCAG 2.2 AA; auditoria formal ainda por realizar.

## Testes

A CI executa ESLint e TypeScript. Testes de componentes, integração BFF e Playwright/E2E ainda estão por acrescentar.

## Estado

Landing page, registo, login e dashboard implementados. O dashboard permite listar, criar, editar e eliminar viagens através do BFF e da API. A edição usa PATCH no BFF, que encaminha o pedido autenticado através do cookie HttpOnly. A validação de ponta a ponta em Docker e browser continua pendente.
