# SKY Design System

## Identidade

**Premium Travel Tech**: uma experiência de viagens contemporânea, clara e confiável, com tecnologia discreta e apontamentos premium.

Referências de qualidade e experiência: Airbnb, Google Flights e Linear. São referências de inspiração, não modelos a copiar.

## Princípios

- Clareza antes de decoração.
- Comparação transparente.
- Hierarquia visual consistente.
- Interações previsíveis.
- Mobile-first e responsividade.
- Acessibilidade WCAG 2.2 AA como objetivo.
- Modos claro e escuro.

## Paleta inicial

| Token | HEX | Papel |
|---|---|---|
| Midnight Navy | `#101D35` | Cor estrutural e superfícies escuras |
| Sky Blue | `#2563EB` | Ação primária |
| Electric Sky | `#38BDF8` | Destaque e foco |
| Cloud White | `#F5F7FB` | Fundo claro |
| Success Green | `#10B981` | Sucesso |
| Amber | `#F59E0B` | Aviso |

A paleta é uma base aprovada; os tokens semânticos e os estados de contraste devem ser validados em ambos os temas.

## Tipografia

- Família principal: Inter.
- Hierarquia tipográfica curta e consistente.
- Preços e métricas com alinhamento tabular sempre que possível.
- Evitar texto pequeno em informação crítica, como condições e encargos.

## Componentes de produto

- `SkyButton`: ações primárias, secundárias e destrutivas.
- `SkyInput`: campos com label, ajuda e erro.
- `SkyDatePicker`: seleção de datas acessível.
- `SkySearchBar`: pesquisa contextual.
- `FlightCard`: itinerário, duração, escalas, bagagem e preço.
- `HotelCard`: localização, avaliação, condições e preço total.
- `PriceBadge`: contexto de preço, não uma promessa de poupança.
- `DestinationCard`: destino e informação editorial.
- `InteractiveMap`: mapa e seleção geográfica.
- `PriceChart`: evolução temporal quando existirem dados.
- `FilterSidebar`: filtros adaptáveis.
- `NavigationBar`: navegação global.

## Cartões de resultados

Os cartões de voos e hotéis devem apresentar, quando a fonte disponibilizar:
- Preço total e moeda.
- Encargos conhecidos e exclusões.
- Horários e duração.
- Escalas e localização.
- Bagagem e condições de alteração/cancelamento.
- Fornecedor e momento da última verificação.

Não esconder condições relevantes atrás de elementos pouco visíveis.

## Estados de interface

Definir estados para loading, vazio, erro, indisponibilidade, dados desatualizados e sucesso. Distinguir claramente preço indicativo de preço confirmado.

## Motion

Usar animações curtas e funcionais. Respeitar `prefers-reduced-motion`. Não usar movimento como substituto de feedback textual ou acessível.

## Ícones e gráficos

- Lucide para ícones consistentes.
- Recharts para gráficos de preço.
- MapLibre GL para mapas, depois de selecionar tiles e geocoding.
- Gráficos devem incluir unidades, intervalos e alternativas textuais.

## Tokens e implementação

Os tokens deverão ser mantidos em `packages/design-tokens` e consumidos pelo frontend. Os componentes partilhados ficarão em `packages/ui` quando a estrutura monorepo estiver implementada.

## Estado

Direção visual aprovada; biblioteca de componentes e tokens ainda não implementados.
