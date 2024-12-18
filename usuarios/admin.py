from django.contrib import admin

from . import models

admin.site.register(models.Estado)
admin.site.register(models.Cidade)
admin.site.register(models.Endereco)
admin.site.register(models.Usuario)
admin.site.register(models.Especialidade)
admin.site.register(models.Profissional)
admin.site.register(models.Servico) 
admin.site.register(models.Avaliacao)
