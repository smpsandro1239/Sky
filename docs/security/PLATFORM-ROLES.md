# SKY — Papéis de acesso

## Papéis globais da plataforma

| Papel | Finalidade | Permissões |
| --- | --- | --- |
| `traveler` | Utilizador normal | Gerir o próprio perfil, pesquisas, favoritos, alertas e viagens onde participa, de acordo com o papel da viagem. |
| `support` | Apoio ao cliente | Consultar a lista administrativa limitada de contas. Não pode alterar papéis nem executar operações de administração. |
| `admin` | Administração da plataforma | Consultar contas e atribuir/remover papéis globais. |

O registo público atribui sempre `traveler`. Um endereço de email numa lista de configuração nunca é prova de titularidade e não concede privilégios. A primeira conta `admin` deve ser provisionada apenas depois de a identidade do titular ser confirmada por um processo operacional seguro; a atribuição deve ser feita por um operador autorizado diretamente na base de dados, sem expor credenciais ou criar endpoints públicos de bootstrap. O início de sessão nunca promove automaticamente uma conta.

## Papéis por viagem

Estes papéis já existem e são independentes do papel global:

| Papel | Finalidade | Permissões |
| --- | --- | --- |
| `owner` | Proprietário da viagem | Controlo total da viagem e gestão de participantes/convites. |
| `editor` | Colaborador | Participar e editar os dados permitidos da viagem. |
| `viewer` | Leitor | Consultar a viagem sem a alterar. |

O proprietário é determinado pela relação da viagem com a conta e não pode ser atribuído como papel de participante. Os convites só podem atribuir `editor` ou `viewer`.

## Endpoints

- `GET /api/v1/admin/users`: lista paginada, apenas `support` e `admin`.
- `PATCH /api/v1/admin/users/{user_id}/role`: alterar papel, apenas `admin`.

A API valida as permissões no servidor. Ocultar controlos no frontend nunca substitui esta validação.

## Salvaguardas

- Papéis desconhecidos são rejeitados pelo schema e pela constraint da base de dados.
- O último administrador ativo não pode ser despromovido.
- Um administrador não pode remover o próprio papel.
- A listagem administrativa nunca devolve hashes de palavras-passe ou tokens.
- Não existe endpoint público para alterar o próprio papel.
