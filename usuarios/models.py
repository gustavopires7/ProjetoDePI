from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Estado(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    sigla = models.CharField(max_length=2, unique=True)

    def __str__(self):
        return self.nome

class Cidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, default=None, null=True, blank=True)

    def __str__(self):
        return f'{self.nome} - {self.estado.sigla}' 

class Endereco(models.Model):
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE)
    rua = models.CharField(max_length=100, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=8, blank=True, null=True)

    def __str__(self):
        return f'{self.cidade.nome} - {self.cidade.estado.sigla}'

class Usuario(AbstractUser):
    telefone = models.CharField(max_length=15, blank=True, null=True)
    telefone_profissional = models.BooleanField(default=False, verbose_name="Este número é WhatsApp profissional?")
    data_nascimento = models.DateField(null=True, blank=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.CASCADE, null=True, blank=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    imagem_perfil = models.ImageField(upload_to='media/usuarios', null=True, blank=True)

    class Meta:
        db_table = 'usuario'

    def delete(self, *args, **kwargs):
        try:
            # Deletar serviços primeiro
            self.servicos_contratados.all().delete()
            
            # Deletar avaliações
            Avaliacao.objects.filter(cliente=self).delete()
            
            # Deletar comentários
            Comentario.objects.filter(autor=self).delete()
            
            # Deletar endereço
            if self.endereco:
                endereco = self.endereco
                self.endereco = None
                self.save()
                endereco.delete()
            
            # Se for profissional, deletar o perfil profissional
            if hasattr(self, 'profissional'):
                self.profissional.delete()
            
            # Por fim, deletar o próprio usuário
            super().delete(*args, **kwargs)
        except Exception as e:
            print(f"Erro ao deletar usuário: {str(e)}")
            raise

    def __str__(self):
        return self.username

class Especialidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Profissional(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE, default=None, null=True, blank=True)
    imagem = models.ImageField(upload_to='media', null=True, blank=True)
    CRM = models.IntegerField(unique=True, default=None)
    biografia = models.TextField(blank=True, null=True)
    preco_servico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def calcular_nota_media(self):
        avaliacoes = self.avaliacoes.all()
        if avaliacoes.exists():
            return avaliacoes.aggregate(models.Avg('nota'))['nota__avg']
        return None
    
    def __str__(self):
        if self.especialidade:
            return f'{self.usuario.username} - {self.especialidade.nome}'
        return self.usuario.username


class Servico(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='servicos')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='servicos_contratados')
    data_agendamento = models.DateTimeField()
    data_realizacao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('AGENDADO', 'Agendado'),
        ('REALIZADO', 'Realizado'),
        ('CANCELADO', 'Cancelado')
    ], default='AGENDADO')

    def __str__(self):
        return f'Profissional: {self.profissional.usuario.username} ({self.profissional.especialidade.nome}) - Cliente: {self.cliente.username}'

class Avaliacao(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='avaliacoes')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    servico = models.OneToOneField(Servico, on_delete=models.CASCADE)
    nota = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    titulo = models.CharField(max_length=100, blank=True, null=True, default='')
    comentario = models.TextField(blank=True, null=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    recomenda = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_avaliacao']

    def __str__(self):
        return f'Avaliação de {self.cliente.get_full_name()} para {self.profissional.usuario.get_full_name()}'

class Comentario(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='respostas')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField()
    data_comentario = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_comentario']

    def __str__(self):
        return f'Comentário de {self.autor.get_full_name()} em {self.data_comentario}'
