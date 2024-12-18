from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import Cidade, Endereco, Especialidade, Estado, Profissional, Usuario


class UsuarioCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'estado' in self.data:
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['cidade'].queryset = Cidade.objects.filter(estado_id=estado_id)
            except (ValueError, TypeError):
                self.fields['cidade'].queryset = Cidade.objects.none()
        elif self.instance.pk:
            self.fields['cidade'].queryset = Cidade.objects.filter(estado=self.instance.estado)

        # Removendo as mensagens de ajuda de senha
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''


    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'})
    )
    first_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        label='Senha'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a senha'}),
        label='Confirmar Senha'
    )
    
    # Campos do usuário adicionais
    telefone = forms.CharField(
        max_length=15, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'})
    )
    data_nascimento = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    # Campos de endereço
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_estado'}),
        required=False
    )
    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_cidade'}),
        required=False
    )
    rua = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da rua'})
    )
    numero = forms.CharField(
        max_length=10, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'})
    )
    bairro = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'})
    )
    cep = forms.CharField(
        max_length=8, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP', 'maxlength': '8'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'telefone', 'estado', 'cidade', 'rua', 'numero', 'bairro', 'telefone', 'cep', 'data_nascimento']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Verificar se as senhas coincidem
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas não coincidem.')

        return cleaned_data

    def _post_clean(self):
        super(forms.ModelForm, self)._post_clean()
        # Pulando a validação de senha do Django
        password = self.cleaned_data.get('password1')
        if password:
            try:
                self.instance.set_password(password)
            except forms.ValidationError as error:
                self.add_error('password2', error)

    def save(self):
        endereco = None
        if any([
            self.cleaned_data.get('estado'), 
            self.cleaned_data.get('cidade'), 
            self.cleaned_data.get('rua'), 
            self.cleaned_data.get('numero'), 
            self.cleaned_data.get('bairro'), 
            self.cleaned_data.get('cep')
        ]):


            endereco = Endereco.objects.create(
                cidade=self.cleaned_data.get('cidade'),
                rua=self.cleaned_data.get('rua'),
                numero=self.cleaned_data.get('numero'),
                bairro=self.cleaned_data.get('bairro'),
                cep=self.cleaned_data.get('cep')
            )

        # Criar usuário
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data.get('username'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('password1'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            telefone=self.cleaned_data.get('telefone'),
            data_nascimento=self.cleaned_data.get('data_nascimento'),            endereco=endereco  # Associa o endereço ao usuário
        )

        return usuario

class UsuarioUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    telefone = forms.CharField(required=False)
    data_nascimento = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    # Campos para endereço - corrigindo os nomes dos campos
    rua = forms.CharField(max_length=200, required=False)  # mudado de logradouro para rua
    numero = forms.CharField(max_length=20, required=False)
    bairro = forms.CharField(max_length=100, required=False)  # adicionado campo bairro
    cep = forms.CharField(max_length=8, required=False)
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.none(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    imagem_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['email', 'telefone', 'data_nascimento', 'imagem_perfil']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Preenche campos iniciais se usuário já tem endereço
        if self.instance.endereco:
            self.fields['rua'].initial = self.instance.endereco.rua  # corrigido
            self.fields['numero'].initial = self.instance.endereco.numero
            self.fields['bairro'].initial = self.instance.endereco.bairro  # adicionado
            self.fields['cep'].initial = self.instance.endereco.cep
            self.fields['estado'].initial = self.instance.endereco.cidade.estado
            self.fields['cidade'].initial = self.instance.endereco.cidade

            # Atualiza cidades de acordo com o estado
            self.fields['cidade'].queryset = Cidade.objects.filter(estado=self.instance.endereco.cidade.estado)
        else:
            self.fields['cidade'].queryset = Cidade.objects.none()

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Atualiza ou cria endereço
            if all([
                self.cleaned_data.get('rua'),  # corrigido
                self.cleaned_data.get('cep'),
                self.cleaned_data.get('estado'),
                self.cleaned_data.get('cidade')
            ]):
                # Se já existe endereço, atualiza
                if user.endereco:
                    endereco = user.endereco
                    endereco.rua = self.cleaned_data['rua']  # corrigido
                    endereco.numero = self.cleaned_data['numero']
                    endereco.bairro = self.cleaned_data['bairro']  # adicionado
                    endereco.cep = self.cleaned_data['cep']
                    endereco.cidade = self.cleaned_data['cidade']
                    endereco.save()
                else:
                    # Se não existe, cria novo endereço
                    endereco = Endereco.objects.create(
                        rua=self.cleaned_data['rua'],  # corrigido
                        numero=self.cleaned_data['numero'],
                        bairro=self.cleaned_data['bairro'],  # adicionado
                        cep=self.cleaned_data['cep'],
                        cidade=self.cleaned_data['cidade']
                    )
                    user.endereco = endereco
                    user.save()
        
        return user
    

class CadastroProfissionalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'estado' in self.data:
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['cidade'].queryset = Cidade.objects.filter(estado_id=estado_id)
            except (ValueError, TypeError):
                self.fields['cidade'].queryset = Cidade.objects.none()
        elif self.instance.pk:
            self.fields['cidade'].queryset = Cidade.objects.filter(estado=self.instance.estado)

        # Removendo as mensagens de ajuda de senha
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''


    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'})
    )
    first_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        label='Senha'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a senha'}),
        label='Confirmar Senha'
    )
    telefone = forms.CharField(
        max_length=15, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'})
    )
    telefone_profissional = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Este número é WhatsApp profissional?'
    )
    data_nascimento = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    CRM = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número do CRM'})
    )
    especialidade = forms.ModelChoiceField(
        queryset=Especialidade.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    biografia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Breve biografia'})
    )
    preco_servico = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Valor do serviço'})
    )
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_estado'}),
        required=False
    )
    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_cidade'}),
        required=False
    )
    rua = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da rua'})
    )
    numero = forms.CharField(
        max_length=10, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'})
    )
    bairro = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'})
    )

    imagem = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Imagem do profissional'})
    )

    cep = forms.CharField(
        max_length=8, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP', 'maxlength': '8'})
    )

    class Meta:
        model = Profissional
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'telefone', 'telefone_profissional', 'CRM', 'especialidade', 'biografia', 'preco_servico', 'estado', 'cidade', 'rua', 'numero', 'bairro', 'telefone', 'cep', 'data_nascimento', 'imagem']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está cadastrado.')
        return username


    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Apenas verifica se as senhas são iguais, sem outras validações
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas não coincidem.')

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean_CRM(self):
        crm = self.cleaned_data.get('CRM')
        if crm and Profissional.objects.filter(CRM=crm).exists():
            raise forms.ValidationError('O CRM informado já está em uso.')
        return crm

    def clean_preco_servico(self):
        preco = self.cleaned_data.get('preco_servico')
        if preco and preco <= 0:
            raise forms.ValidationError('O preço do serviço deve ser maior que zero.')
        return preco

    def save(self):
        endereco = None
        if any([
            self.cleaned_data.get('estado'), 
            self.cleaned_data.get('cidade'), 
            self.cleaned_data.get('rua'), 
            self.cleaned_data.get('numero'), 
            self.cleaned_data.get('bairro'), 
            self.cleaned_data.get('cep')
        ]):
            
        

            endereco = Endereco.objects.create(
                cidade=self.cleaned_data.get('cidade'),
                rua=self.cleaned_data.get('rua'),
                numero=self.cleaned_data.get('numero'),
                bairro=self.cleaned_data.get('bairro'),
                cep=self.cleaned_data.get('cep')
            )

        usuario = Usuario.objects.create_user(
            username=self.cleaned_data.get('username'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('password1'),  # A senha será salva sem validações adicionais
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            telefone=self.cleaned_data.get('telefone'),
            telefone_profissional=self.cleaned_data.get('telefone_profissional'),  # Adicionando este campo
            data_nascimento=self.cleaned_data.get('data_nascimento'),
            endereco=endereco
        )

        profissional = Profissional.objects.create(
            usuario=usuario,
            CRM=self.cleaned_data.get('CRM'),
            especialidade=self.cleaned_data.get('especialidade'),
            biografia=self.cleaned_data.get('biografia'),
            preco_servico=self.cleaned_data.get('preco_servico'),
        )

        return profissional
