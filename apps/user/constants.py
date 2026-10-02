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
}

ADMIN_PROFILE_CODE = "admin"
