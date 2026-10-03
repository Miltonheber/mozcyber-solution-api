from django.contrib import admin

admin.site.site_header = "Administração"
admin.site.site_title = "Administração"
admin.site.index_title = "Modelos"


class AuditedAdmin(admin.ModelAdmin):
    """Base dos admins de modelos `BaseModel`: preenche `created_by`/`updated_by` (como o `BaseRepository`)
    e mostra a auditoria só de leitura."""

    audit_fields = ("created_at", "updated_at", "created_by", "updated_by")
    list_per_page = 25

    def get_readonly_fields(self, request, obj=None):
        return (*super().get_readonly_fields(request, obj), *self.audit_fields)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ReadOnlyAdmin(admin.ModelAdmin):
    """Registos históricos (logs, análises): consulta apenas, sem criar, editar nem apagar."""

    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
