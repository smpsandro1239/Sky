# Segurança e Privacidade SKY

## Objetivo

Definir uma linha de base de segurança e privacidade para o desenvolvimento do SKY. Este documento é uma política de conceção; não certifica que os controlos estejam implementados.

## Gestão de segredos

- Nunca guardar chaves, passwords, tokens ou credenciais no Git.
- Fornecer apenas um `.env.example` com nomes e valores fictícios.
- Utilizar variáveis de ambiente ou um gestor de segredos nos ambientes implantados.
- Rodar credenciais em caso de exposição.
- Restringir permissões das credenciais por ambiente e finalidade.

## Autenticação e autorização

- Adotar um mecanismo de autenticação mantido e revisto.
- Aplicar autorização no servidor, por recurso e proprietário.
- Proteger operações administrativas com permissões específicas.
- Definir expiração, revogação e rotação de sessões/tokens.
- Não confiar em verificações feitas apenas no frontend.

## Dados pessoais

- Recolher apenas os dados necessários.
- Definir finalidade, retenção e eliminação.
- Limitar acesso interno por necessidade.
- Evitar dados pessoais em logs, métricas e mensagens de erro.
- Disponibilizar processos para pedidos de acesso, correção e apagamento, conforme obrigações legais aplicáveis.

## Pagamentos futuros

- Utilizar prestador de pagamentos especializado.
- Não armazenar PAN completo nem CVV.
- Validar assinaturas dos webhooks.
- Deduplicar eventos e aplicar idempotência.
- Manter auditoria e reconciliação de estados.
- Avaliar obrigações PCI DSS e requisitos legais com o prestador e especialistas competentes.

## Segurança da API

- HTTPS em ambientes expostos.
- Validação estrita de entrada.
- Proteção contra abuso e rate limiting.
- CORS com origens permitidas explicitamente.
- Timeouts e limites de tamanho.
- Proteção contra SSRF ao integrar serviços externos.
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

A implementação deverá ser avaliada face ao RGPD e legislação aplicável na UE, incluindo bases legais, transparência, direitos dos titulares, contratos com subcontratantes e transferências internacionais quando existam.

## Processo de resposta a incidentes

Documentar deteção, contenção, análise, recuperação, comunicação e lições aprendidas. Segredos expostos devem ser revogados/rodados imediatamente.

## Estado

Baseline de segurança planeada. Os controlos precisam de ser implementados, testados e auditados.
