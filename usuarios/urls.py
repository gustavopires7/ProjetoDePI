from django.urls import path

from .views import (
    IndexView,
    ProfessionalRegisterView,
    ProfileDeleteView,
    ProfileEditView,
    ProfileView,
    ProfissionalDetalhesView,
    UserLoginView,
    UserLogoutView,
    UserRegisterView,
    carregar_cidades,
    tipo_usuario,
    adicionar_comentario,
    adicionar_avaliacao,
    enviar_email_agendamento,
    excluir_comentario,
    excluir_avaliacao,
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('usuario/tipo/', tipo_usuario, name='tipo_usuario'),
    path('cadastro/cliente/', UserRegisterView.as_view(), name='register_client'),
    path('cadastro/profissional/', ProfessionalRegisterView.as_view(), name='register_professional'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('perfil/', ProfileView.as_view(), name='profile'),
    path('perfil/editar/', ProfileEditView.as_view(), name='profile_edit'),
    path('perfil/excluir/', ProfileDeleteView.as_view(), name='profile_delete'),
    path('carregar-cidades/', carregar_cidades, name='carregar_cidades'),
    path('profissional/detalhes/<int:pk>/', ProfissionalDetalhesView.as_view(), name='profissional_detalhes'),
    path('avaliacao/<int:avaliacao_id>/comentar/', adicionar_comentario, name='adicionar_comentario'),
    path('profissional/<int:profissional_id>/avaliar/', adicionar_avaliacao, name='adicionar_avaliacao'),
    path('profissional/<int:profissional_id>/agendar/', enviar_email_agendamento, name='enviar_email_agendamento'),
    path('comentario/<int:comentario_id>/excluir/', excluir_comentario, name='excluir_comentario'),
    path('avaliacao/<int:avaliacao_id>/excluir/', excluir_avaliacao, name='excluir_avaliacao'),
]