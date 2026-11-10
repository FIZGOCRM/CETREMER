# 🎓 CETREMER — Plataforma de Ensino & Vídeos

Plataforma completa de cursos online, streaming de aulas em vídeo, área do aluno, portal do criador/produtor e fórum de comunidade, desenvolvida em **Python + Django**.

---

## 🚀 Como Rodar o Projeto na Nova Máquina

Siga o passo a passo abaixo para configurar e executar o projeto em uma nova máquina (macOS, Linux ou Windows).

### 1. Pré-requisitos
* **Python 3.9+** instalado ([python.org](https://www.python.org/downloads/))
* **Git** instalado

---

### 2. Clonar ou Copiar o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd CETREMER
```

---

### 3. Criar e Ativar o Ambiente Virtual (venv)

* **No macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

* **No Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

---

### 4. Instalar as Dependências
Com o `venv` ativado, instale todas as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

---

### 5. Configurar as Variáveis de Ambiente
Copie o arquivo de exemplo para criar o seu `.env`:
```bash
cp .env.example .env
```
*(No Windows PowerShell use `copy .env.example .env`)*

Preencha `SECRET_KEY` e `FIELD_ENCRYPTION_KEY` antes de iniciar. Gere valores únicos:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

O `DEBUG` usa `False` por padrão fora do ambiente local. Guarde as chaves do `.env`: dados criptografados dependem de `FIELD_ENCRYPTION_KEY` para leitura.

---

### 6. Banco de Dados e Dados Iniciais
O banco SQLite local (`db.sqlite3`) não é versionado. Para criar a base com os dados de demonstração:
```bash
python manage.py migrate
python manage.py loaddata data_dump.json
```

`python seed.py` recria os dados de demonstração e apaga usuários, cursos e matrículas locais; use apenas quando quiser reiniciar a base.

---

### 7. Iniciar o Servidor
Execute o servidor de desenvolvimento:
```bash
python manage.py runserver 8000
```

Acesse no navegador:
👉 **http://localhost:8000**

---

## 🔑 Usuários e Acessos Pré-cadastrados (Seed)

| Perfil | Usuário / E-mail | Senha | Descrição |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` (`admin@cetremer.com.br`) | `password123` | Painel `/painel/` e Django Admin `/admin/` |
| **Produtor / Criador** | `john_creator` (`john@creator.com`) | `password123` | Painel `/painel/` |
| **Aluno** | `jane_student` (`jane@student.com`) | `password123` | Acesso à Área do Aluno & Aulas (`/dashboard`) |

---

## 🧭 Principais Rotas do Sistema

* **Catálogo & Landing Page:** `http://localhost:8000/`
* **Área do Aluno (Player de Vídeo e Aulas):** `http://localhost:8000/dashboard/`
* **Painel de gestão:** `http://localhost:8000/painel/`
* **Comunidade & Fórum de Discussão:** `http://localhost:8000/community/`
* **Administração técnica do Django:** `http://localhost:8000/admin/`

Para incorporar vídeos do Vimeo, configure em cada vídeo **Privacidade > Incorporar > Somente em domínios que eu escolher** e inclua o domínio de produção e `localhost`.

---

## 📦 Estrutura de Pastas

```text
CETREMER/
├── community/          # Fórum, tópicos e comentários da comunidade
├── core/               # Configurações centrais do Django (settings, urls, wsgi)
├── courses/            # Modelos de cursos, módulos, lições e player de vídeo
├── sales/              # Pedidos e checkout
├── users/              # Modelos de usuários, perfis de criador e aluno
├── media/              # Uploads de capas de cursos e mídias
├── static/             # Arquivos CSS, JS e imagens da aplicação
├── templates/          # Templates HTML do sistema
├── data_dump.json      # Backup completo dos dados em formato JSON
├── requirements.txt    # Lista de dependências Python
├── .env.example        # Modelo de variáveis de ambiente
├── db.sqlite3          # Banco de dados local SQLite
├── manage.py           # Utilitário de comando do Django
└── seed.py             # Script para resetar e popular banco de teste
```
