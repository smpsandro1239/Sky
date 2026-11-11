# Deploy do SKY com Vercel, Render e Neon

Esta configuração mantém o frontend Next.js na Vercel, aloja a API FastAPI no Render e utiliza PostgreSQL gerido pelo Neon. O PostgreSQL atual não é convertido para SQLite/Turso.

## Arquitetura

- **Vercel:** frontend Next.js já publicado.
- **Render:** serviço web Docker para `apps/api`.
- **Neon:** PostgreSQL gerido, fora do Render.
- **GitHub:** repositório, histórico e GitHub Actions.

O ficheiro `render.yaml` define o serviço `sky-api` no plano gratuito do Render, na região de Frankfurt, e solicita a variável `DATABASE_URL` durante a criação do Blueprint. O segredo `SKY_SECRET_KEY` é gerado pelo Render.

## 1. Criar a base de dados Neon

1. Criar uma conta em [Neon](https://neon.com/).
2. Criar um projeto PostgreSQL, preferencialmente na região de Frankfurt para reduzir a latência entre API e base de dados.
3. Criar/selecionar a base de dados e o role da aplicação.
4. Abrir **Connect** e copiar a connection string PostgreSQL.
5. Guardar a string como segredo. Nunca a colocar no GitHub, no código frontend ou em ficheiros públicos.

A aplicação instala `psycopg 3` e normaliza automaticamente os formatos `postgresql://` e `postgres://` para `postgresql+psycopg://`. Mantém os parâmetros TLS fornecidos pelo Neon, como `sslmode=require`.

Para esta primeira implantação, utilizar a ligação direta do Neon para que as migrações Alembic possam correr sem depender de funcionalidades de sessão de um pooler. Se a carga justificar, avaliar depois a ligação pooled e a configuração do pool SQLAlchemy.

## 2. Criar o serviço Render

1. Confirmar que o commit com `render.yaml` está na branch `main`.
2. Criar conta em [Render](https://render.com/).
3. Escolher **New → Blueprint** e ligar o repositório `smpsandro1239/Sky`.
4. O Render deve detetar `render.yaml` e propor o serviço `sky-api`.
5. Quando solicitado, fornecer `DATABASE_URL` copiada do Neon.
6. Confirmar o plano Free e a região Frankfurt antes de criar.
7. Aguardar pelo build e pelo deploy.

O Dockerfile executa `alembic upgrade head` antes de iniciar o Uvicorn e utiliza a porta `PORT` fornecida pelo Render (com fallback local para 8000).

## 3. Verificar a API

Depois do primeiro deploy, abrir:

```text
https://<nome-do-servico>.onrender.com/api/v1/health
```

A resposta esperada é semelhante a:

```json
{"status":"ok","service":"sky-api","version":"0.1.0"}
```

O health check confirma que a API responde. Confirmar também nos logs do Render que `alembic upgrade head` terminou sem erros. Não partilhar os logs se contiverem connection strings ou segredos.

## 4. Ligar a Vercel à nova API

No projeto frontend da Vercel, adicionar/alterar a variável de ambiente:

- `API_INTERNAL_URL` = URL base do serviço Render, sem barra final e sem `/api/v1`.

Exemplo:

```text
API_INTERNAL_URL=https://sky-api.onrender.com
```

O nome real do domínio depende do nome atribuído ao serviço no Render. Fazer redeploy do frontend depois de alterar a variável.

O frontend utiliza o BFF Next.js para encaminhar os pedidos autenticados. O token de sessão permanece num cookie HttpOnly e a URL/credenciais da base de dados ficam exclusivamente no servidor.

## 5. Variáveis opcionais

Configurar no Render apenas quando forem necessárias:

- `AMADEUS_CLIENT_ID` e `AMADEUS_CLIENT_SECRET` para pesquisa de voos/alojamentos.
- `AMADEUS_BASE_URL` com `https://test.api.amadeus.com` para sandbox.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_STARTTLS` e `SMTP_USE_SSL` para envio de convites por email.
- Credenciais Google OAuth, quando a funcionalidade estiver configurada.

Não adicionar valores secretos ao `render.yaml`. Introduzi-los no painel seguro do Render.

## 6. Limitações do plano gratuito

- O Render Free suspende serviços web após um período sem tráfego; o primeiro pedido seguinte pode demorar a responder.
- O plano gratuito é adequado a desenvolvimento, demonstrações e testes, não a disponibilidade garantida.
- Os planos gratuitos têm limites de utilização e podem mudar; confirmar os limites atuais nos painéis dos fornecedores.
- A suspensão da API não deve eliminar os dados PostgreSQL alojados no Neon.

## 7. Migração e segurança

- Não apontar a API de produção para uma base de dados vazia sem confirmar o estado dos dados atuais.
- Se existirem dados no PostgreSQL atual, fazer backup e planear a transferência para Neon antes de mudar o frontend.
- Nunca executar migrações destrutivas para resolver divergências sem backup.
- Manter a API antiga disponível até validar login, viagens, participantes, convites, despesas, pagamentos, pesquisa e favoritos no novo ambiente.
- Não declarar o deploy concluído apenas porque o Blueprint foi criado; confirmar build, migrações, health check e testes ponta a ponta.

## Referências oficiais

- [Render Blueprints](https://render.com/docs/blueprint-spec)
- [Render Health Checks](https://render.com/docs/health-checks)
- [Neon — ligar a aplicação](https://neon.com/docs/get-started/connect-neon)
