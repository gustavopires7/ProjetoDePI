from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.decorators.http import require_POST
from datetime import datetime  # Adicionar este import
from django.core.mail import send_mail
from django.conf import settings

from .forms import CadastroProfissionalForm, UsuarioCreationForm, UsuarioUpdateForm
from .models import Cidade, Especialidade, Profissional, Usuario, Avaliacao, Comentario, Servico  # Adicionando o import do Servico


class IndexView(TemplateView):
    template_name = 'usuarios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtros existentes
        nome = self.request.GET.get('nome', '').strip()
        especialidade = self.request.GET.get('especialidade', '').strip()
        
        # Novo: ordenação
        ordem = self.request.GET.get('ordem', 'nome')
        
        profissionais = Profissional.objects.all()
        
        # Aplicar filtros
        if nome:
            profissionais = profissionais.filter(usuario__username__icontains=nome)
        if especialidade:
            profissionais = profissionais.filter(especialidade_id=especialidade)
        
        
        
        paginator = Paginator(profissionais, 4)
        page_number = self.request.GET.get('page', 1)

        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            raise Http404("Página não encontrada")
        
        context.update({
            "page_obj": page_obj,
            "profissionais": page_obj.object_list,
            "especialidades": Especialidade.objects.all(),
            "is_paginated": page_obj.has_other_pages(),
            
        })
        return context

class UserRegisterView(CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cliente_form.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)

class ProfessionalRegisterView(CreateView):
    model = Profissional
    form_class = CadastroProfissionalForm
    template_name = 'usuarios/profissional_form.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        print(form.errors)
        form.save()
        return HttpResponseRedirect(self.success_url)

class UserLoginView(TemplateView):
    template_name = 'usuarios/login.html'

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, self.template_name, {'error': 'Credenciais inválidas'})

class UserLogoutView(TemplateView):
    def get(self, request):
        logout(request)
        return redirect('login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/profile.html'
    login_url = 'login'

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/form.html'
    success_url = reverse_lazy('profile')
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

class ProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'usuarios/confirm_delete.html'
    success_url = reverse_lazy('login')
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            # Primeiro fazer logout do usuário
            logout(request)
            # Depois deletar o usuário usando o método personalizado
            user.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            print(f"Erro ao deletar usuário: {str(e)}")
            return HttpResponseRedirect(reverse_lazy('profile'))

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

def tipo_usuario(request):
    return render(request, 'usuarios/selecao_usuario.html')


def carregar_cidades(request):
    estado_id = request.GET.get('estado')
    cidades = Cidade.objects.filter(estado_id=estado_id).values('id', 'nome')
    return JsonResponse(list(cidades), safe=False)

class ProfissionalDetalhesView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/profissional_detalhes.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Busca o profissional pelo ID fornecido na URL
        profissional_id = self.kwargs.get('pk')  # Assumindo que o ID é passado como parte da URL
        context['profissional'] = get_object_or_404(Profissional, pk=profissional_id)
        return context

@require_POST
def adicionar_comentario(request, avaliacao_id):
    try:
        avaliacao = Avaliacao.objects.get(id=avaliacao_id)
        texto = request.POST.get('texto')
        
        if texto:
            comentario = Comentario.objects.create(
                avaliacao=avaliacao,
                autor=request.user,
                texto=texto
            )
            
            return JsonResponse({
                'status': 'success',
                'comentario': {
                    'autor': comentario.autor.get_full_name(),
                    'texto': comentario.texto,
                    'data': comentario.data_comentario.strftime("%d/%m/%Y"),
                }
            })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def adicionar_avaliacao(request, profissional_id):
    try:
        profissional = get_object_or_404(Profissional, id=profissional_id)
        
        # Verificar se o usuário já avaliou este profissional
        if Avaliacao.objects.filter(profissional=profissional, cliente=request.user).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Você já avaliou este profissional'
            }, status=400)

        # Criar serviço automaticamente
        servico = Servico.objects.create(
            profissional=profissional,
            cliente=request.user,
            data_agendamento=datetime.now(),
            data_realizacao=datetime.now(),
            status='REALIZADO'
        )

        # Criar avaliação
        avaliacao = Avaliacao.objects.create(
            profissional=profissional,
            cliente=request.user,
            servico=servico,  # Associando o serviço criado
            nota=request.POST.get('nota'),
            titulo=request.POST.get('titulo', ''),
            comentario=request.POST.get('comentario', ''),
            recomenda=request.POST.get('recomenda', 'true') == 'true'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Avaliação enviada com sucesso!',
            'avaliacao': {
                'autor': avaliacao.cliente.get_full_name(),
                'nota': avaliacao.nota,
                'titulo': avaliacao.titulo,
                'comentario': avaliacao.comentario,
                'data': avaliacao.data_avaliacao.strftime("%d/%m/%Y"),
                'recomenda': avaliacao.recomenda
            }
        })
    except Exception as e:
        print(f"Erro ao adicionar avaliação: {str(e)}")  # Para debug
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao enviar avaliação'
        }, status=400)

@require_POST
def excluir_comentario(request, comentario_id):
    try:
        comentario = get_object_or_404(Comentario, id=comentario_id)
        if request.user == comentario.autor:
            comentario.delete()
            return JsonResponse({'status': 'success', 'message': 'Comentário excluído com sucesso!'})
        return JsonResponse({
            'status': 'error',
            'message': 'Você não tem permissão para excluir este comentário'
        }, status=403)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_POST
def excluir_avaliacao(request, avaliacao_id):
    try:
        avaliacao = get_object_or_404(Avaliacao, id=avaliacao_id)
        
        # Verifica se o usuário é o dono da avaliação
        if request.user == avaliacao.cliente:
            # Exclui o serviço associado também
            if avaliacao.servico:
                avaliacao.servico.delete()
            avaliacao.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Avaliação excluída com sucesso!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Você não tem permissão para excluir esta avaliação'
            }, status=403)
    except Exception as e:
        print(f"Erro ao excluir avaliação: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao excluir avaliação'
        }, status=400)

def enviar_email_agendamento(request, profissional_id):
    profissional = get_object_or_404(Profissional, id=profissional_id)
    gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={profissional.usuario.email}&su=Solicitação de Agendamento&body=Olá Dr(a). {profissional.usuario.get_full_name()}, gostaria de agendar uma consulta."
    return JsonResponse({'status': 'success', 'gmail_link': gmail_link})