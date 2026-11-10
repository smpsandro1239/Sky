# Arquitetura Frontend SKY

## Objetivos

Criar uma experiência responsiva, rápida e acessível para descobrir destinos, pesquisar voos e alojamentos, comparar opções e organizar viagens.

## Stack proposta

- Next.js e React.
- TypeScript com configuração estrita.
- Tailwind CSS e shadcn/ui como base de componentes.
- Lucide para ícones.
- Motion para animações funcionais e discretas.
- Recharts para visualização de preços.
- MapLibre GL para mapas, sujeito à escolha de fornecedor de tiles/geocoding.

As versões serão fixadas durante a implementação após validação de compatibilidade.

## Organização proposta

```text
apps/web/
├── public/
├── src/
│   ├── app/
│   ├── components/
│   │   ├── layout/
│   │   ├── search/
│   │   ├── flights/
│   │   ├── hotels/
│   │   ├── recommendations/
│   │   └── ui/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── styles/
│   └── types/
└── tests/
```

A estrutura poderá ser ajustada quando os fluxos reais e os limites entre funcionalidades estiverem implementados.

## Rotas previstas

- `/`: página inicial e pesquisa.
- `/flights`: resultados de voos.
- `/hotels`: resultados de alojamento.
- `/destinations`: descoberta de destinos.
- `/trips`: viagens guardadas e planeador.
- `/favorites`: favoritos.
- `/account`: perfil e preferências.

As rotas protegidas exigem autenticação quando esta estiver implementada.

## Componentes de produto

- `SkyButton`
- `SkyInput`
- `SkyDatePicker`
- `SkySearchBar`
- `FlightCard`
- `HotelCard`
- `PriceBadge`
- `DestinationCard`
- `InteractiveMap`
- `PriceChart`
- `FilterSidebar`
- `NavigationBar`

Os componentes de domínio devem receber dados tipados e não fazer chamadas diretas a fornecedores.

## Estado e dados

- Estado local para interações isoladas.
- Estado de URL para filtros e pesquisas partilháveis.
- Camada de serviços para comunicação com a API.
- Cache de pedidos e invalidação definidos por funcionalidade.
- Não guardar tokens sensíveis em localStorage.

## Design e acessibilidade

- Mobile-first e layouts adaptáveis.
- Modos claro e escuro.
- Contraste e navegação por teclado.
- Labels, foco visível e mensagens de erro acessíveis.
- Objetivo de conformidade WCAG 2.2 AA.
- Respeitar redução de movimento do sistema operativo.

## Testes

- Vitest para lógica e componentes.
- Testing Library para interações.
- Playwright para fluxos críticos: pesquisa, filtros, favoritos e autenticação.

## Estado

Arquitetura proposta. A aplicação frontend ainda não está implementada.
