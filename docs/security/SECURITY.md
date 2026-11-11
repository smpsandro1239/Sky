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
- Os endpoints privados validam o token e confirmam que o utilizador existe e está ativo.
- As operações de viagens, voos, alojamentos, despesas e partilhas validam o papel do utilizador (proprietário, editor ou leitor) no servidor.
- Só o proprietário pode gerir participantes, convites, papéis, metadados e orçamento da viagem.
- Os tokens de convite são aleatórios, armazenados como hash SHA-256, têm validade de 7 dias e são de utilização única.
- O envio de convites por email é opcional e usa SMTP configurado por ambiente. Quando ativado, exige STARTTLS ou SSL; host e remetente têm de ser definidos em conjunto e as credenciais têm de estar completas.
- A API devolve `email_sent` para distinguir o envio concluído de um convite criado apenas para partilha manual. Falhas de SMTP não invalidam o convite nem expõem credenciais.
- O frontend usa Route Handlers Next.js como BFF.
- O JWT é guardado num cookie `HttpOnly`, `SameSite=Lax`, com `Secure` em produção e expiração limitada ao tempo de vida do token.
- O token não é exposto ao JavaScript do browser nem guardado em localStorage.
- O endpoint BFF de leitura tem uma allowlist dos recursos autorizados.

Pendências antes de produção:
- Testes de integração e E2E do ciclo completo de autenticação e do envio SMTP num ambiente de teste controlado.
- Estratégia de revogação/rotação de sessões e refresh tokens.
- Rate limiting e proteção contra tentativas automatizadas de login.
- Revisão de CSRF para operações mutáveis e política de origem.
- Política de recuperação de conta e verificação de email.

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

Existem controlos iniciais de autenticação, autorização e gestão de sessão via cookie HttpOnly. A solução ainda não foi auditada nem está pronta para produção.
