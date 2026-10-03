"""Catálogo de permissões do sistema. Ao criar um endpoint novo, adicione o código aqui:
o comando `seed_access` cria-os na BD e atribui todos ao perfil `admin`."""

PERMISSION_CATALOG = {
    "user:read": "Listar/ver utilizadores",
    "user:create": "Criar utilizadores",
    "user:update": "Editar utilizadores",
    "user:delete": "Remover utilizadores",
    "profile:read": "Listar/ver perfis",
    "profile:create": "Criar perfis",
    "profile:update": "Editar perfis",
    "profile:delete": "Remover perfis",
    "permission:read": "Listar/ver permissões",
    "permission:create": "Criar permissões",
    "permission:update": "Editar permissões",
    "permission:delete": "Remover permissões",
    "log:read": "Consultar logs de auditoria",
    "blacklist:read": "Listar/ver números na blacklist",
    "blacklist:update": "Moderar números (confirmar/limpar)",
    "report:read": "Listar/ver denúncias",
    "report:update": "Moderar denúncias",
    "education:read": "Listar/ver conteúdo educativo (inclui rascunhos)",
    "education:create": "Criar conteúdo educativo",
    "education:update": "Editar conteúdo educativo",
    "education:delete": "Remover conteúdo educativo",
    "occurrence:create": "Criar ocorrências de documentos perdidos",
    "occurrence:read": "Consultar ocorrências de documentos perdidos",
    "occurrence:update": "Actualizar ocorrências",
}

ADMIN_PROFILE_CODE = "admin"
POLICE_PROFILE_CODE = "esquadra"
ENTITY_PROFILE_CODE = "entidade"

# Perfis operacionais criados pelo seed (o admin recebe sempre todas as permissões).
SEED_PROFILES = {
    POLICE_PROFILE_CODE: ("Esquadra", ["occurrence:create", "occurrence:read", "occurrence:update"]),
    ENTITY_PROFILE_CODE: ("Entidade interessada", ["occurrence:read"]),
}
