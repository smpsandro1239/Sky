# Segurança e Privacidade SKY

## Objetivo

Definir a linha de base de segurança e documentar os controlos já implementados. Este documento não representa uma auditoria nem uma certificação de segurança.

## Gestão de segredos

- Não guardar chaves, passwords, tokens ou credenciais reais no Git.
- Utilizar `.env.example` apenas com valores demonstrativos.
- Utilizar variáveis de ambiente ou um gestor de segredos nos ambientes implantados.
- Rodar credenciais em caso de exposição.
- Restringir permissões por ambiente e finalidade.

## Autenticação e autorização — estado atual

- A API emite JWT após autenticação bem-sucedida.
- Os endpoints privados validam o JWT, confirmam que o utilizador existe e está ativo e verificam a sessão persistida na base de dados.
- As operações de viagens, voos, alojamentos, despesas e partilhas validam o papel do utilizador (proprietário, editor ou leitor) no servidor.
- Só o proprietário pode gerir participantes, convites, papéis, metadados e orçamento da viagem.
- Os tokens de convite são aleatórios, armazenados como hash SHA-256, têm validade de 7 dias e são de utilização única.
- O envio de convites por email é opcional e usa SMTP configurado por ambiente. Quando ativado, exige STARTTLS ou SSL; host e remetente têm de ser definidos em conjunto e as credenciais têm de estar completas.
- A API devolve `email_sent` para distinguir o envio concluído de um convite criado apenas para partilha manual. Falhas de SMTP não invalidam o convite nem expõem credenciais.
- O frontend usa Route Handlers Next.js como BFF.
- O JWT é guardado num cookie `HttpOnly`, `SameSite=Lax`, com `Secure` em produção e expiração limitada ao tempo de vida do token.
- Cada sessão tem um identificador próprio (`sid`); a API guarda apenas o hash SHA-256 do JWT, a validade e o estado de revogação. Cada pedido autenticado confirma a sessão persistida, permitindo invalidar um token individual sem terminar as restantes sessões do utilizador.
- O endpoint de logout revoga a sessão actual na API; o BFF encaminha o token do cookie para esse endpoint antes de o eliminar.
- O token não é exposto ao JavaScript do browser nem guardado em localStorage.
- O BFF tem uma allowlist explícita de recursos e métodos autorizados.
- As operações mutáveis encaminhadas pelo BFF, incluindo login e logout, exigem um cabeçalho `Origin` igual à origem do pedido; quando `Sec-Fetch-Site` existe, tem de ser `same-origin`.
- Pedidos mutáveis sem `Origin`, com origem diferente ou identificados pelo browser como cross-site/same-site são rejeitados com HTTP 403, antes de executar a operação ou alterar cookies de sessão.

Pendências antes de produção:
- Testes de integração e E2E do ciclo completo de autenticação e do envio SMTP num ambiente de teste controlado.
- Listagem e revogação remota de sessões por dispositivo, rotação de tokens e eventual introdução de refresh tokens.
- Rate limiting e proteção contra tentativas automatizadas de login.
- Testes E2E de CSRF no browser e validação da política de origem em todos os domínios/proxies de produção.
- Política de recuperação de conta e verificação de email.

## Papéis globais da plataforma

- `traveler` é o papel atribuído por defeito a todas as novas contas.
- `support` permite apenas consulta limitada de contas através do endpoint administrativo.
- `admin` permite consultar contas e gerir papéis globais.
- A atribuição inicial de administrador depende de uma allowlist operacional `SKY_ADMIN_EMAILS`; não existe autoatribuição pública.
- Os papéis por viagem (`owner`, `editor`, `viewer`) são independentes dos papéis globais.
- A API aplica RBAC no servidor e a base de dados restringe os valores de papel aceites.
- O último administrador ativo não pode ser despromovido e um administrador não pode remover o próprio papel.

## Dados pessoais

- Recolher apenas os dados necessários.
- Definir finalidade, retenção e eliminação.
- Limitar acesso interno por necessidade.
- Evitar dados pessoais em logs, métricas e mensagens de erro.
- As credenciais SMTP são configuradas por variáveis de ambiente e não devem ser versionadas; o serviço evita registar endereços de destinatários em mensagens de falha.
- Implementar processos para direitos dos titulares conforme obrigações legais.

## Pagamentos futuros

- Utilizar prestador de pagamentos especializado.
- Não armazenar PAN completo nem CVV.
- Validar assinaturas dos webhooks.
- Deduplicar eventos e aplicar idempotência.
- Manter auditoria e reconciliação de estados.
- Avaliar PCI DSS e requisitos legais com prestador e especialistas competentes.

## Segurança da API

- HTTPS em ambientes expostos.
- Validação estrita de entrada.
- Rate limiting e limites de tamanho.
- CORS com origens permitidas explicitamente.
- Timeouts para fornecedores externos.
- Proteção contra SSRF nas integrações.
- Não expor erros internos nem documentação sensível em produção sem decisão explícita.

## Dependências e cadeia de fornecimento

- Fixar versões e usar lockfiles.
- Analisar vulnerabilidades em CI.
- Atualizar dependências de forma controlada.
- Rever imagens Docker e respetiva origem.
- Evitar executar containers como root quando possível.

## Backups e continuidade

- Definir política de backup e retenção.
- Encriptar backups e restringir acesso.
- Testar restauros periodicamente.
- Definir objetivos de recuperação antes de produção.

## Conformidade

A implementação deverá ser avaliada face ao RGPD e legislação aplicável na UE, incluindo bases legais, transparência, direitos dos titulares, contratos com subcontratantes e transferências internacionais.

## Processo de resposta a incidentes

Documentar deteção, contenção, análise, recuperação, comunicação e lições aprendidas. Segredos expostos devem ser revogados/rodados imediatamente.

## Estado

Existem controlos iniciais de autenticação, autorização, sessões persistidas com revogação individual e gestão de sessão via cookie HttpOnly. A solução ainda não foi auditada nem está pronta para produção.
