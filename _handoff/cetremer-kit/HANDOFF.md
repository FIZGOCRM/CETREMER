# Handoff · Redesign completo da plataforma CETREMER

Documento para o agente que vai implementar. Leia inteiro antes de escrever código. Ele foi escrito para que nenhum valor de CSS, nome de classe, rota ou comportamento precise ser adivinhado.

Stack do projeto (já existente, não mudar): Django 4.2, Django Templates, CSS puro, JS vanilla, SQLite em desenvolvimento, sem build de assets. Apps: `core`, `users`, `courses`, `sales`, `community`.

---

## 0. O que vem neste kit

| Caminho no kit | O que é | Para onde vai no repositório |
| --- | --- | --- |
| `static/css/cetremer.css` | CSS final e completo do design system. Fonte única de estilos. | `static/css/cetremer.css` |
| `static/js/site.js` | Comportamentos gerais (filtro, copiar, imprimir, diálogo, campo secreto, dropzone, lista editável). | `static/js/site.js` |
| `static/js/aluno.js` | Página da aula: acordeão, concluir aula, Vimeo. Substitui `netflix.js`. | `static/js/aluno.js` |
| `static/js/painel-grade.js` | Arrastar para reordenar aulas e módulos no admin. | `static/js/painel-grade.js` |
| `templates/base_core.html` | Esqueleto HTML (fontes, CSS, site.js). | `templates/base_core.html` |
| `templates/base_public.html` | Layout das páginas públicas (cabeçalho e rodapé do site). | `templates/base_public.html` |
| `templates/base_aluno.html` | Layout da área do aluno (menu lateral claro). | `templates/base_aluno.html` |
| `templates/base_admin.html` | Layout do painel administrativo (menu lateral escuro). | `templates/base_admin.html` |
| `templates/partials/*.html` | Ícones, menus, mensagens, barra de progresso, cards de curso. | `templates/partials/` |
| `python/courses/templatetags/cetremer.py` | Filtros `brl`, `duracao`, `mmss`, `cpf`, `iniciais`, `codigo_cert` e tag `pct`. | `courses/templatetags/cetremer.py` |
| `python/users/validators.py` | `validate_cpf` e `only_digits`. | `users/validators.py` |
| `referencia/*.dc.html` | As 25 telas aprovadas, com todos os valores exatos. Referência visual, não é código para copiar. | Não copiar para o repositório. |

Sobre os arquivos `referencia/*.dc.html`: são exportações do canvas de design. Ignore os invólucros `<x-dc>`, `<helmet>`, o `<script src="./support.js">` e o `<script type="text/x-dc">`. O que importa é o HTML de dentro: ordem dos blocos, textos, hierarquia e os valores dos `style=""`. Cada valor de `style` dessas telas já existe como classe em `cetremer.css`. Seu trabalho é reproduzir a estrutura usando as classes, nunca copiar os `style=""`.

Tabela de correspondência entre telas de referência e templates:

| Referência | Template Django | Base |
| --- | --- | --- |
| `Landing.dc.html` | `templates/landing.html` | `base_public.html` |
| `CursoPreview.dc.html` | `templates/courses/course_preview.html` | `base_public.html` |
| `Checkout.dc.html` | `templates/sales/checkout.html` | `base_public.html` |
| `Login.dc.html` | `templates/login.html` | `base_core.html` |
| `Cadastro.dc.html` | `templates/register.html` | `base_core.html` |
| `EsqueciSenha.dc.html` | `templates/registration/password_reset_form.html` e `password_reset_done.html` | `base_core.html` |
| `RedefinirSenha.dc.html` | `templates/registration/password_reset_confirm.html` | `base_core.html` |
| `VerificarCertificado.dc.html` | `templates/courses/certificate_verify.html` | `base_public.html` |
| `Main.dc.html` | `templates/courses/dashboard.html` | `base_aluno.html` |
| `Aula.dc.html` | `templates/courses/lesson_detail.html` | `base_core.html` (layout próprio) |
| `AoVivo.dc.html` | `templates/courses/live_classes.html` | `base_aluno.html` |
| `Certificados.dc.html` | `templates/courses/certificates.html` | `base_aluno.html` |
| `Certificado.dc.html` | `templates/courses/certificate.html` | `base_core.html` (layout próprio) |
| `CertificadoBloqueado.dc.html` | `templates/courses/certificate_error.html` | `base_core.html` (layout próprio) |
| `Comunidade.dc.html` | `templates/community/hub.html` | `base_aluno.html` |
| `MinhaConta.dc.html` | `templates/users/settings.html` | `base_aluno.html` |
| `AdminPainel.dc.html` | `templates/painel/dashboard.html` | `base_admin.html` |
| `AdminCursos.dc.html` | `templates/painel/courses.html` | `base_admin.html` |
| `AdminCursoEditar.dc.html` | `templates/painel/course_form.html` | `base_admin.html` |
| `AdminGrade.dc.html` | `templates/painel/course_lessons.html` | `base_admin.html` |
| `AdminAlunos.dc.html` | `templates/painel/students.html` | `base_admin.html` |
| `AdminImportar.dc.html` | `templates/painel/students_import.html` | `base_admin.html` |
| `AdminPedidos.dc.html` | `templates/painel/orders.html` | `base_admin.html` |
| `AdminComunidade.dc.html` | `templates/painel/community.html` | `base_admin.html` |
| `AdminConfiguracoes.dc.html` | `templates/painel/settings.html` | `base_admin.html` |

---

## 1. Regras inegociáveis

1. **Um único CSS.** Carregar só `static/css/cetremer.css` (já está em `base_core.html`). Remover `main.css`, `components.css` e todos os blocos `<style>` dos templates. Não usar Bootstrap, Tailwind nem qualquer framework.
2. **Sem `style=""` nos templates.** Uma única exceção: a largura da barra de progresso (`style="width: N%"`), já resolvida em `partials/progress.html`. Imagens de capa entram como `<img>` com classe, nunca como `background-image` inline.
3. **Valor que não existir em `cetremer.css`:** não invente. Pegue o valor exato do `style=""` na tela de referência e crie uma classe nova no fim de `cetremer.css`, numa seção `/* 29. Extras */`, com nome no mesmo padrão. Registre no PR.
4. **Cores só por token.** Nunca escrever hexadecimal fora do bloco `:root`. O azul claro `#0099FF` (`--c-progress`) é só para barras de progresso; texto e botões usam `--c-primary` `#0B63C4`, porque o claro não passa em contraste.
5. **Fontes:** Montserrat 700 e 800 só para títulos de destaque (classes `display`, `page-title`, `topbar__title`, `section__title`, etc.). Todo o resto é Inter 400, 500, 600 e 700. Já carregadas em `base_core.html`.
6. **Ícones:** só pelo `partials/icon.html`. Nada de emoji em nenhum template (o MVP atual usa vários: remover todos).
7. **Idioma e formatos:** pt-BR. Dinheiro sempre com `|brl` (R$ 1.234,56). Duração com `|duracao`. CPF com `|cpf`. Datas com `|date:"d/m/Y"` e horas com `|date:"H:i"`. `TIME_ZONE = "America/Campo_Grande"`, `USE_TZ = True`.
8. **Acessibilidade mínima (vale para toda tela):**
   - um único `<h1>` por página (nos layouts aluno e admin, o `<h1>` é o `topbar__title`);
   - todo campo com `<label for>`; campo sem rótulo visível usa `<label class="sr-only">`;
   - botão só com ícone tem `aria-label`;
   - item ativo do menu e aula atual com `aria-current="page"`;
   - botões que abrem e fecham com `aria-expanded`;
   - alvos de toque com no mínimo 44px (as classes já garantem).
9. **Não quebrar o que funciona:** os testes em `courses/tests.py` buscam os textos "Custom Banner Title", "Certificado Bloqueado", "CERTIFICADO" e "Aluno Certificado". Antes de mexer num template, rode `grep -rn "assertContains" */tests.py` e mantenha cada texto. Se um texto mudar de propósito, atualize o teste no mesmo commit e explique.
10. **Checkout:** o gateway está sendo integrado em paralelo. No `sales/checkout.html`, preserve todos os `id` e `name` usados por `checkout.js` e por `process_checkout` (lista na seção 6.3). Só troque a casca visual.
11. **Nada de dado inventado na interface.** Prova social, notas, número de alunos e frases de exemplo do MVP saem. O que não existir no banco não aparece.

---

## 2. Arquitetura de templates

```
templates/
  base_core.html            <html>, <head>, fontes, cetremer.css, site.js. Blocos: title, meta_description, extra_css, body_class, body, extra_js
  base_public.html          estende core. Blocos: header, header_nav, content, footer, footer_class
  base_aluno.html           estende core. Blocos: page_title, topbar_actions, page_class, content, footer
  base_admin.html           estende core. Blocos: admin_title, topbar_class, topbar_eyebrow, page_title, topbar_actions, page_class, content
  partials/
    icon.html               ícones SVG
    sidebar_aluno.html      menu lateral do aluno (ativo por request.resolver_match.url_name)
    sidebar_admin.html      menu lateral do admin (namespace "painel")
    messages.html           alertas (django.contrib.messages e as variáveis antigas error/success)
    progress.html           barra de progresso acessível
    course_card_owned.html  card de curso do aluno
    course_card_shop.html   card de curso à venda
  landing.html, login.html, register.html
  registration/             telas de senha (views nativas do Django)
  courses/                  dashboard, lesson_detail, course_preview, live_classes, certificates, certificate, certificate_error, certificate_verify
  community/hub.html
  users/settings.html
  sales/checkout.html
  painel/                   telas do admin (novo)
```

Os templates em `templates/creator/` deixam de existir no fim (fase 7). As rotas `/creator/...` passam a redirecionar (301) para `/painel/...`.

### 2.1 Context processor obrigatório

Criar `core/context_processors.py` e registrar em `TEMPLATES[0]["OPTIONS"]["context_processors"]`:

```python
from users.models import SiteSettings  # ver seção 4.1

def site(request):
    return {"site": SiteSettings.load()}
```

Todos os layouts usam `site.school_name`, `site.whatsapp_url`, `site.terms_url`, `site.privacy_url`.

### 2.2 Como carregar JS por página

- `site.js` já vem em todas (defer, no `<head>`).
- `aluno.js`: só em `lesson_detail.html`, no bloco `extra_js`, depois do player do Vimeo:
  ```django
  {% block extra_js %}
  <script src="https://player.vimeo.com/api/player.js"></script>
  <script src="{% static 'js/aluno.js' %}"></script>
  {% endblock %}
  ```
- `painel-grade.js`: só em `painel/course_lessons.html`.
- `checkout.js`: só em `sales/checkout.html` (manter o arquivo atual).
- Remover `netflix.js` e os scripts inline de `course_preview.html` no fim (fase 7).

---

## 3. Tokens e componentes

Tudo está em `cetremer.css`, organizado em seções numeradas. Abaixo, o mapa de uso. A coluna "Usar quando" é a regra para escolher a classe.

### 3.1 Cores (seção 1 do CSS)

| Token | Valor | Usar quando |
| --- | --- | --- |
| `--c-ink` | #0F1B2D | texto principal, botão escuro, faixa de CTA, menu do admin |
| `--c-text-2` | #3A4556 | texto secundário forte, itens de menu |
| `--c-muted` | #5B6472 | legendas e metadados |
| `--c-bg` | #F4F6F9 | fundo das áreas logadas |
| `--c-surface` / `--c-surface-2` | #FFFFFF / #F8FAFC | cards / cabeçalhos de tabela e módulo |
| `--c-border` / `--c-border-strong` / `--c-border-soft` | #E3E8EF / #C9D3DF / #EEF1F5 | borda de card / borda de input e botão secundário / divisória entre linhas |
| `--c-primary` / `--c-primary-strong` / `--c-primary-soft` | #0B63C4 / #034C8C / #E8F2FC | ação e link / marca e hover / fundo de ativo |
| `--c-progress` | #0099FF | só barras de progresso |
| `--c-teal` / `--c-teal-soft` | #0E5A66 / #E3F3F5 | categoria Especialidades médicas |
| `--c-slate` | #3B4A5E | capa da categoria Para leigos |
| `--c-success*`, `--c-warning*`, `--c-danger*` | ver CSS | estados |

### 3.2 Componentes principais

| Componente | Classes | Observação |
| --- | --- | --- |
| Botão principal | `btn btn--primary` | 44px. Grande: `+ btn--lg` (48px), CTA: `+ btn--xl` (52px) |
| Botão secundário | `btn btn--secondary` | borda #C9D3DF |
| Botão contorno azul | `btn btn--outline` | "Começar curso", "Publicar dúvida", "Atualizar senha" |
| Botão escuro | `btn btn--dark` | "Entrar no Google Meet" na faixa ao vivo |
| Botão claro (fundo escuro) | `btn btn--light` | CTA da landing |
| Botão discreto | `btn btn--quiet` | "Sair" no topo |
| Botão de link azul | `btn btn--ghost` | "Ver agenda" |
| Concluída | `btn btn--done` | estado do botão de concluir aula |
| Texto vermelho | `btn btn--danger-text` | "Excluir aula" |
| Remover acesso | `btn--link-danger` | link vermelho pequeno |
| Botão pequeno | `+ btn--sm` (40px) / `+ btn--xs` (36px) | "Editar", "Renomear", "Substituir" |
| Largura total | `+ btn--block` | cards de curso |
| Botão só ícone | `icon-btn` | com `aria-label` |
| Campo | `field` > `field__label` + `input` / `select` / `textarea` + `hint` ou `error-text` | input 48px |
| Campo inválido | `aria-invalid="true"` no input + `<span class="error-text" id="...">` ligado por `aria-describedby` | borda 2px vermelha |
| Grade de campos | `form-grid` (mín. 240px), `form-grid--200`, `--180`, `--160`; item largo `span-all` | |
| Checkbox | `check` (bloco) ou `check check--inline` | |
| Liga/desliga | `toggle-row` | label inteiro clicável |
| Opção de pagamento | `radio-cards` > `radio-card` | selecionado por `:has(input:checked)` |
| Chave salva | `secret-field` + `secret-field__value` | ver seção 4.8 |
| Upload | `dropzone` / `dropzone--lg` | com `data-dropzone` |
| Card | `card` + `card--pad` (24) / `--pad-lg` (28) / `--pad-md` (22) / `--pad-sm` (20) / `--clip` | |
| Etiqueta | `badge` + `badge--blue/teal/gray/success/warning/danger`; tamanhos `badge--md`, `badge--lg` | |
| Progresso | `partials/progress.html` + `progress-label` | `size="lg"` = 8px |
| Alerta | `alert alert--error/success/warning/info`; `alert--lg`, `alert--banner` | |
| Vazio | `empty`, `empty--sm`, `empty--dashed` | |
| Tabela | `table-wrap` > `table table--wNNN` | sempre dentro de `table-wrap` (rola no celular) |
| Filtros | `toolbar` (busca + selects) e `chips` > `chip` com `aria-pressed` | |
| Indicador | `metric-grid` > `metric` (`metric__label`, `metric__value`, `metric__foot`) | `metric--sm` em Pedidos |
| Passo numerado | `step-head` > `step-num` + `step-title` | |
| Avatar | `avatar` (44), `avatar--32/52/64`, `avatar--soft`, `avatar--gray` | iniciais com `|iniciais` |

### 3.3 Utilitários

Só os da seção 3 do CSS: `stack`, `row`, `row--between`, `row--end`, `row--baseline`, `row--start`, `gap-N` (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 40), `grow`, `mt-auto`, `self-start`, `self-end`, `text-12` a `text-18`, `fw-500/600/700`, `muted`, `text-2`, `text-ink`, `text-primary`, `text-success`, `text-danger`, `text-center`, `text-right`, `nowrap`, `mono`, `display`, `link-plain`, `link-strong`, `sr-only`.

Exemplo de bloco de texto com título e subtítulo:
```html
<div class="stack gap-4">
  <h2 class="card__title">Dados para o certificado</h2>
  <span class="card__sub">Confira com atenção: é exatamente assim que sai no certificado.</span>
</div>
```

### 3.4 Ícones

```django
{% include "partials/icon.html" with name="play" %}
{% include "partials/icon.html" with name="check" size=16 stroke="2.4" %}
```

Nomes disponíveis: `grid`, `video`, `chat`, `award`, `user`, `users`, `home`, `course`, `receipt`, `gear`, `play` (preenchido), `play-circle`, `clock`, `check`, `check-circle`, `circle`, `chevron-left`, `chevron-right`, `chevron-up`, `chevron-down`, `lock`, `file`, `download`, `link`, `alert`, `mail`, `pulse`, `plus-circle`, `x`, `drag` (preenchido).

Tamanhos usados no design: 20 (menus, padrão), 18 (botões e alertas), 16 (metadados), 14 (etiquetas), 13 e 11 (dentro do `status-dot`).

---

## 4. Backend necessário

Cada item abaixo diz o que criar e por quê. Migrations novas, sempre reversíveis. Atualizar `data_dump.json` e o seed no fim de cada fase que mexer em modelo.

### 4.1 Modelos

**`courses.Category` (novo)**
```python
class Category(models.Model):
    COLOR_CHOICES = [("blue", "Azul"), ("teal", "Verde-azulado"), ("slate", "Cinza")]
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default="blue")
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ["order", "name"]

    @property
    def badge_class(self):
        return {"blue": "badge--blue", "teal": "badge--teal", "slate": "badge--gray"}[self.color]
```
Seed: "Essenciais AHA" (blue, 1), "Especialidades médicas" (teal, 2), "Para leigos" (slate, 3). Remover os slugs fixos de `courses/views.py` (linhas 99 a 105) e as variáveis `essentials`, `specialties`, `leigos`.

**`courses.Course` (campos novos)**
| Campo | Tipo | Uso |
| --- | --- | --- |
| `category` | `ForeignKey(Category, null=True, blank=True, on_delete=SET_NULL)` | etiqueta e filtro |
| `short_name` | `CharField(max_length=12, blank=True)` | sigla da capa sem imagem: BLS, ACLS, PALS, DEA, "Plantão" |
| `cover_color` | `CharField(max_length=10, blank=True, choices=blue, blue-2, teal, slate, ink)` | cor da capa sem imagem; vazio usa a cor da categoria |
| `workload_hours` | `PositiveIntegerField(null=True, blank=True)` | carga horária (certificado, cards, venda) |
| `learning_objectives` | `TextField(blank=True)` | um objetivo por linha |
| `target_audience` | `TextField(blank=True)` | "Para quem é este curso" |
| `live_calendar_url` | `URLField(blank=True)` | substitui `live_schedule_embed` (seção 4.9) |

Propriedades:
```python
@property
def cover_class(self):
    color = self.cover_color or (self.category.color if self.category else "blue")
    return f"cover--{color}"

@property
def objectives_list(self):
    return [line.strip() for line in self.learning_objectives.splitlines() if line.strip()]
```
Seed: BLS 8h (cover blue), ACLS 16h (blue-2), PALS 16h (teal), DEA 4h (slate), Plantão Sem GPT sem carga definida (ink). Remover "Duração: Xh" do texto das descrições, porque agora é campo.

Capa: novo padrão é **3:2, mínimo 1200 × 800 px**. As capas atuais são 3:4 e serão cortadas por `object-fit: cover` até a cliente reenviar.

**`courses.Lesson` (campos novos)**
| Campo | Tipo | Uso |
| --- | --- | --- |
| `vimeo_id` | `CharField(max_length=20, blank=True)` | preenchido no `save()` a partir de `video_url` |
| `vimeo_hash` | `CharField(max_length=40, blank=True)` | parâmetro `h` de vídeos não listados |

`download_url` e `download_name` migram para o modelo novo abaixo (data migration) e depois são removidos.

**`courses.LessonMaterial` (novo)**
```python
class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="materials", on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to="materials/", blank=True)
    url = models.URLField(blank=True)  # para os links antigos migrados
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ["order", "id"]
```
Aceitar só PDF no upload (validar extensão e `content_type`), tamanho máximo 20 MB (configurável em settings `MATERIAL_MAX_MB`).

**`courses.Enrollment` (campos novos)**
- `source`: `CharField(choices=[("purchase","Compra no site"),("import","Importado"),("manual","Liberado pelo admin"),("signup","Cadastro no site")], default="manual")`
- `last_accessed_at`: `DateTimeField(null=True, blank=True)`, atualizado em toda abertura de aula.

**`courses.Certificate` (novo)**
```python
class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.PROTECT, related_name="certificate")
    code = models.CharField(max_length=12, unique=True)        # 12 caracteres hex maiúsculos, secrets.token_hex(6).upper()
    student_name = models.CharField(max_length=200)            # cópia no momento da emissão
    student_cpf = models.CharField(max_length=11)              # só dígitos
    course_title = models.CharField(max_length=200)
    workload_hours = models.PositiveIntegerField(null=True)
    completed_at = models.DateTimeField()                      # data da última aula concluída
    issued_at = models.DateTimeField(auto_now_add=True)
```
Os dados ficam congelados: se o curso mudar de nome depois, o certificado continua igual.

**`community.CommunityPost` (campos novos)**
- `lesson`: `ForeignKey("courses.Lesson", null=True, blank=True, on_delete=SET_NULL)` para as dúvidas da aula.
- `is_hidden`: `BooleanField(default=False)`.
- Propriedade `is_answered`: existe `Comment` deste post feito por usuário com `is_staff` ou `role in ("ADMIN", "CREATOR")`.

**`sales.Order`**: acrescentar o status `REFUNDED` ("Reembolsado"). Rótulos na interface: `COMPLETED` → "Pago" (`badge--success`), `PENDING` → "Aguardando" (`badge--warning`), `FAILED` → "Recusado" (`badge--danger`), `REFUNDED` → "Reembolsado" (`badge--gray`).

**`users.StudentProfile`**: `cpf` passa a guardar só dígitos e a validar com `validate_cpf` do kit. O campo `address` sai da interface (o modelo fica até a cliente decidir; não exibir, não exigir).

**`users.SiteSettings` (novo, registro único)**
```python
class SiteSettings(models.Model):
    school_name = models.CharField(max_length=80, default="CETREMER")
    logo = models.ImageField(upload_to="site/", blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)          # só dígitos com DDI, ex. 5567999999999
    terms_url = models.URLField(blank=True)
    privacy_url = models.URLField(blank=True)
    access_period_text = models.CharField(max_length=120, blank=True)  # FAQ "Por quanto tempo tenho acesso?"
    # Pagamentos
    gateway_name = models.CharField(max_length=30, blank=True)
    gateway_key_encrypted = models.TextField(blank=True)
    gateway_sandbox = models.BooleanField(default=True)
    # E-mail
    email_from_name = models.CharField(max_length=80, default="CETREMER")
    email_from = models.EmailField(blank=True)
    email_host = models.CharField(max_length=120, blank=True)
    email_port = models.PositiveIntegerField(default=587)
    email_username = models.CharField(max_length=120, blank=True)
    email_password_encrypted = models.TextField(blank=True)
    email_use_tls = models.BooleanField(default=True)
    # Certificado
    signer_name = models.CharField(max_length=120, blank=True)
    signer_role = models.CharField(max_length=120, blank=True)        # "Médico · CRM-MS 00000"
    signature_image = models.ImageField(upload_to="site/", blank=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_url(self):
        return f"https://wa.me/{self.whatsapp}" if self.whatsapp else ""
```
Migrar o número de WhatsApp hoje fixo nos templates (`5567996494740`) para `whatsapp`.

`CreatorProfile` deixa de ser usado pela interface. Não apagar ainda; tirar os campos de segredo do `ModelAdmin` dele.

### 4.2 Papéis e acesso

- A plataforma é de um cliente só. O painel `/painel/` é acessível por `is_staff` ou `role in ("ADMIN", "CREATOR")`.
- Criar o decorator `core/decorators.py`:
  ```python
  def painel_required(view):
      @wraps(view)
      @login_required
      def wrapper(request, *args, **kwargs):
          u = request.user
          if u.is_staff or getattr(u, "role", "") in ("ADMIN", "CREATOR"):
              return view(request, *args, **kwargs)
          raise PermissionDenied
      return wrapper
  ```
- O painel lista **todos** os cursos (não filtrar por `creator`). Curso novo grava `creator=request.user`.
- `/admin/` (Django Admin) continua só para superusuário, como ferramenta de suporte.

### 4.3 Autenticação

- **Login por e-mail.** Criar `users/backends.py` com `EmailBackend` (autentica por `email__iexact`; se não achar, tenta `username`, para o admin antigo). Colocar antes do `ModelBackend` em `AUTHENTICATION_BACKENDS`. O campo do formulário continua com `name="username"`, mas com `type="email"` e rótulo "E-mail", então a view de login não muda.
- **Cadastro:** campos nome completo, e-mail, senha, confirmar senha e aceite dos termos (obrigatório). `username` é gerado a partir do e-mail (parte antes do @ + sufixo numérico se existir). Grava `StudentProfile.full_name`. Validar senha com `validate_password`. `Enrollment` não é criado no cadastro.
- **Recuperar senha:** usar as views nativas `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, `PasswordResetCompleteView`, nas rotas:
  | Rota | Nome |
  | --- | --- |
  | `/senha/esqueci/` | `password_reset` |
  | `/senha/enviado/` | `password_reset_done` |
  | `/senha/nova/<uidb64>/<token>/` | `password_reset_confirm` |
  | `/senha/pronto/` | `password_reset_complete` (redireciona para `login` com `messages.success("Senha criada. Entre com seu e-mail e a nova senha.")`) |
  Templates de e-mail em `templates/registration/password_reset_email.txt` e `password_reset_subject.txt`, em português. O mesmo fluxo serve para o **primeiro acesso** de alunos importados (seção 4.7).
- **E-mail:** criar `core/email_backend.py` com um backend que lê `SiteSettings` na hora do envio (host, porta, usuário, senha descriptografada, TLS, remetente "Nome <email>"). Se não houver host configurado, cai no `console` backend em DEBUG e registra erro em produção.

### 4.4 Vídeo (Vimeo)

- `Lesson.save()`: interpretar `video_url` nestes formatos e preencher `vimeo_id` e `vimeo_hash`:
  `https://vimeo.com/123456789`, `https://vimeo.com/123456789/abcdef1234`, `https://player.vimeo.com/video/123456789?h=abcdef1234`.
- Duração automática: ao salvar no painel com URL nova, buscar `https://vimeo.com/api/oembed.json?url=<video_url>` (timeout 5 s, `urllib.request`). Se vier `duration`, gravar em `duration_seconds`. Se falhar, manter o valor manual e mostrar `hint` "Não conseguimos ler a duração. Informe em minutos." no formulário (campo de minutos aparece só nesse caso).
- URL do player (montada no backend, propriedade `Lesson.player_url`):
  `https://player.vimeo.com/video/{vimeo_id}?h={vimeo_hash}&dnt=1&title=0&byline=0&portrait=0` (omitir `h=` se vazio).
- Markup do player (seção 6.10). Atributos obrigatórios no iframe: `allow="autoplay; fullscreen; picture-in-picture"`, `allowfullscreen`, `referrerpolicy="strict-origin-when-cross-origin"`, `title="Vídeo da aula: {{ lesson.title }}"`.
- O seed usa YouTube. Manter compatibilidade: se `video_url` for YouTube, usar o embed atual dentro do mesmo `.player`, com o mesmo `referrerpolicy`. Sem vídeo: `<div class="player__empty">Vídeo ainda não disponível.</div>`.
- **Configuração no Vimeo (anotar no README):** em cada vídeo, Privacidade > "Incorporar" > "Somente em domínios que eu escolher", com o domínio de produção e `localhost`.

### 4.5 Progresso e navegação

- **Ordem da aula no curso:** `lessons = Lesson.objects.filter(module__course=course).order_by("module__order", "order", "id")`. Use sempre essa ordem.
- **Próxima aula do aluno** (`next_lesson`): primeira aula dessa ordem que não está concluída. Se todas estão, a última.
- **Anterior e próxima** na página da aula: vizinhas de `lesson` nessa ordem (`prev_lesson`, `next_lesson_nav`; `None` nas pontas).
- **Por módulo:** `module.lessons_list`, `module.done_count`, `module.total_count` calculados na view (anotar com `Count` ou montar em Python; não fazer query por aula no template).
- **Endpoint novo e idempotente** para o Vimeo: `POST /courses/lesson/<id>/complete/` (nome `complete_lesson`). Marca como concluída sem alternar. Mesma checagem de matrícula do `toggle_progress` e mesmo JSON de resposta:
  `{"is_completed": true, "completed_count": 2, "total_count": 4, "percentage": 50.0}`.
- O `toggle_progress` continua para o botão (alterna). O template passa a URL por `data-url="{% url 'toggle_progress' lesson.id %}"`; `aluno.js` não monta URL nenhuma.
- **Pontos e nível (gamificação):** saem da interface. Não exibir em lugar nenhum. A lógica no backend pode ficar.

### 4.6 Certificado

- `issue_certificate(slug)`:
  1. exige matrícula (já feito);
  2. calcula `completed_count`, `total`, `pct`;
  3. `data_ok = bool(profile.full_name) and validate_cpf(profile.cpf) passa`;
  4. se `pct < 100` ou não `data_ok`: renderiza `certificate_error.html` com `course`, `completed_count`, `total`, `remaining`, `pct`, `next_lesson`, `progress_ok`, `data_ok`;
  5. senão: `Certificate.objects.get_or_create(enrollment=...)` com os dados congelados e renderiza `certificate.html` com `certificate`, `site`, `verify_url`.
- `verify_url = request.build_absolute_uri(reverse("verify_certificate")) + "?codigo=" + certificate.code`.
- **Verificação pública:** `GET /certificado/verificar/` (nome `verify_certificate`), sem login. Lê `?codigo=` (aceita com ou sem hífens, maiúsculo ou minúsculo). Contexto: `query`, `certificate` (ou `None`), `searched` (bool). Nunca mostrar CPF nessa página.
- **Baixar PDF:** sem biblioteca nova. O botão chama `window.print()` (`data-print`) e o CSS de impressão (seção 27) gera A4 paisagem. Texto do botão: "Baixar PDF".
- **Lista do aluno:** `GET /certificados/` (nome `certificates`): um item por matrícula com `course`, `pct`, `completed`, `total`, `remaining`, `certificate` (ou `None`).

### 4.7 Painel administrativo (`/painel/`, namespace `painel`)

Criar o app `painel` (ou módulo `courses/painel_views.py` com `painel/urls.py`). Todas as views com `@painel_required`.

| Rota | Nome (`painel:`) | Método | Função |
| --- | --- | --- | --- |
| `/painel/` | `dashboard` | GET | indicadores e listas recentes |
| `/painel/cursos/` | `courses` | GET | lista com busca `?q=` e `?categoria=` |
| `/painel/cursos/novo/` | `course_new` | GET, POST | formulário vazio |
| `/painel/cursos/<id>/` | `course_edit` | GET, POST | editar curso |
| `/painel/cursos/<id>/aulas/` | `course_lessons` | GET, POST | grade; `?aula=<id>` abre a aula no painel lateral; `?nova=<module_id>` abre formulário de aula nova |
| `/painel/cursos/<id>/aulas/ordem/` | `course_reorder` | POST JSON | recebe o payload do `painel-grade.js` |
| `/painel/alunos/` | `students` | GET, POST | lista com `?q=`, `?curso=`, `?aluno=<id>` abre o detalhe; POST com `action` |
| `/painel/alunos/exportar/` | `students_export` | GET | CSV com nome, e-mail, CPF, cursos |
| `/painel/alunos/importar/` | `students_import` | GET, POST | 3 passos (seção 6.22) |
| `/painel/pedidos/` | `orders` | GET | lista com `?q=`, `?status=`, `?periodo=` |
| `/painel/pedidos/exportar/` | `orders_export` | GET | CSV |
| `/painel/comunidade/` | `community` | GET, POST | abas `?aba=pendentes|respondidos|ocultos` |
| `/painel/configuracoes/` | `settings` | GET, POST | `SiteSettings` |

Ações POST de alunos (`action`): `enroll` (aluno + curso, cria usuário se o e-mail não existir e manda e-mail de primeiro acesso), `unenroll` (remove `Enrollment`, mantém progresso no banco), `resend_access` (e-mail de primeiro acesso). Sempre `messages.success` com texto claro e redirect para a mesma URL com `?aluno=<id>`.

Redirecionar (301) `/creator/` → `/painel/`, `/creator/course/new/` → `painel:course_new`, `/creator/course/<id>/edit/` → `painel:course_edit`, `/creator/course/<id>/builder/` → `painel:course_lessons`, `/creator/payments/` e `/creator/integrations/` → `painel:settings`.

### 4.8 Segredos (crítico 4)

- Dependência nova: `cryptography` (fixar versão no `requirements.txt`).
- `core/crypto.py` com `encrypt(text)` e `decrypt(token)` usando `Fernet(settings.FIELD_ENCRYPTION_KEY)`. A chave vem do ambiente (`.env`); documentar no `.env.example` como gerar (`Fernet.generate_key()`).
- Os campos `*_encrypted` nunca vão para o template. A view passa só:
  - `gateway_key_last4` (últimos 4 caracteres) ou `None`;
  - `email_password_set` (bool).
- No formulário, o input de chave só aparece depois de "Substituir" (`site.js`, item 5). Input vazio no POST = manter a chave atual. Nunca usar `value=` em input de segredo.
- Remover do `CreatorProfileAdmin` os campos de chave e senha.
- `.gitignore`: `db.sqlite3` e `.env` fora do repositório a partir de agora (gerar o seed por `loaddata data_dump.json`).

### 4.9 Agenda das aulas ao vivo (crítico 6)

- Trocar `live_schedule_embed` (HTML cru com `|safe`) por `live_calendar_url` (URL).
- Data migration: extrair o `src` do iframe antigo, se houver.
- Propriedade `Course.calendar_embed_url`: aceitar só host `calendar.google.com`; pegar o parâmetro `src` e montar
  `https://calendar.google.com/calendar/embed?src=<src>&ctz=America/Campo_Grande&mode=AGENDA&showTitle=0&showPrint=0&showTabs=0&showCalendars=0&showTz=0`.
  Host diferente: retornar vazio e o formulário mostra erro "Use o link público de uma agenda do Google".
- Nenhum `|safe` em conteúdo vindo de usuário em toda a plataforma. Rodar `grep -rn "|safe" templates/` no fim e justificar cada ocorrência.

### 4.10 Importação de alunos

- Aceitar `.csv` (UTF-8 com ou sem BOM; se falhar, Latin-1). Delimitador detectado com `csv.Sniffer` entre `,` e `;`.
- Cabeçalhos aceitos (sem acento, minúsculo, comparar após normalizar):
  - nome: `nome`, `name`, `nome completo`, `cliente`, `comprador`, `nome do comprador`, `nome do cliente`
  - e-mail: `email`, `e-mail`, `email do comprador`, `email do cliente`
  - CPF: `cpf`, `documento`, `cpf/cnpj`, `documento do comprador`
  Os nomes reais das exportações da Eduzz e da Hotmart devem ser conferidos com um arquivo real assim que a cliente enviar; acrescente os que faltarem nessa lista.
- Passo 1 e 2 (POST com arquivo e cursos): validar cada linha e guardar a prévia na sessão (`request.session["import_preview"]`, máximo 5.000 linhas). Situação por linha: "Novo aluno", "Já cadastrado" (ganha os cursos), "E-mail inválido" ou "E-mail repetido no arquivo" (ignorados).
- Passo 3 (POST `confirm`): criar usuários com `set_unusable_password()`, `StudentProfile.full_name` e `cpf` (só se vazio e válido), `Enrollment(source="import")`. Se "Enviar e-mail de acesso agora" estiver marcado, mandar o e-mail de primeiro acesso (link do `password_reset_confirm`, assunto "Seu acesso à CETREMER"). Limpar a sessão e mostrar `messages.success("N alunos importados. M já existiam e receberam os cursos.")`.

---

## 5. Comportamentos de JS (prontos no kit)

| Arquivo | Comportamento | Contrato no HTML |
| --- | --- | --- |
| `site.js` | Filtro por categoria | botões `chip` com `data-filter="slug"` ou `data-filter="all"` e `aria-pressed`; cards com `data-category="slug"` |
| `site.js` | Copiar link | `<button data-copy="URL"><span data-label>Texto</span></button>` |
| `site.js` | Imprimir | `data-print` |
| `site.js` | Diálogo | `data-dialog-open="id"` e, dentro do `<dialog class="dialog" id="id">`, `data-dialog-close` |
| `site.js` | Campo secreto | ver seção 6.25 |
| `site.js` | Upload | `<label class="dropzone" data-dropzone>` com `<input type="file" class="sr-only">` e `<span data-dropzone-name>` |
| `site.js` | Lista editável | `data-repeater`, `data-repeater-list`, `data-repeater-item`, `data-repeater-remove`, `data-repeater-add`, `<template data-repeater-template>` |
| `aluno.js` | Acordeão, concluir, Vimeo | ver seção 6.10 |
| `painel-grade.js` | Reordenar | ver seção 6.20 |

---

## 6. Tela a tela

Para cada tela: rota, contexto que a view entrega, estrutura com classes e estados. A ordem dos blocos e os textos fixos são os da referência indicada. Textos entre colchetes nas referências são placeholders de dado real.

### 6.1 Landing · `Landing.dc.html`

- Rota `/` (nome `landing`). Contexto: `hero` (HeroBanner ativo), `categories`, `courses` (publicados, `select_related("category")`).
- `{% block content %}`:
  1. `section.container.hero` > `div.hero__text` (`span.pill-eyebrow` "Aprenda fazendo, com quem faz", `h1.hero__title` = `{{ hero.title }}`, `p.hero__lead` = `{{ hero.subtitle }}`, `div.row.gap-12` com `a.btn.btn--primary.btn--xl` = `hero.primary_button_text`/`url` e `a.btn.btn--secondary.btn--xl` = `hero.whatsapp_button_text`/`url`) + `div.hero__media` com `<img src="{{ hero.background_image.url }}" alt="">` (se houver vídeo, `<video autoplay muted loop playsinline>`; sem nenhum, o div fica só com o fundo azul claro).
     O título vem do HeroBanner, por isso o teste "Custom Banner Title" continua passando.
  2. `section.stats` > `div.container.stats__grid` com 3 `div.stats__item` (`span.stats__value` + `span.stats__label`): "+2.000 / alunos capacitados", "AHA / cursos credenciados", "100% / prático e aplicado". Conteúdo fixo a confirmar com a cliente.
  3. `section#cursos.container.section-block`: `div.section-block__head` (`h2.section-block__title` "Nossos treinamentos", `p.muted` "Do suporte básico para leigos aos protocolos avançados da AHA."), `div.chips.chips--10` com `button.chip.chip--lg[data-filter=all][aria-pressed=true]` "Todos" + um por categoria, `div.course-grid.course-grid--230` com `{% include "partials/course_card_shop.html" with course=c cta="Ver curso" %}`.
  4. `div.band-muted` > `section#diferenciais.container.section-block`: título "Por que treinar na CETREMER", `div.feature-grid` com 3 `div.feature` (`span.icon-tile` com ícones `pulse`, `plus-circle`, `award`; `h3.feature__title`; `p.feature__text`). Textos na referência.
  5. `section#empresas.container.section-block` > `div.cta-band` (`div.cta-band__text` com `h2.cta-band__title` "Capacite sua equipe hospitalar" e `p.cta-band__lead`; `a.btn.btn--light.btn--xl` "Solicitar proposta pelo WhatsApp" para `site.whatsapp_url`).
- Remover: barra azul do topo, botão flutuante de WhatsApp, seção "Cursos em alta", emojis.

### 6.2 Página do curso · `CursoPreview.dc.html`

- Rota `/courses/<slug>/` (nome `course_preview`). Contexto: `course`, `modules` (com aulas), `total_lessons`, `total_seconds`, `has_materials`, `is_enrolled`, `next_lesson`.
- `{% block header_nav %}` só com "Cursos". `{% block footer_class %}site-footer--compact{% endblock %}`.
- `section.course-hero` > `div.container.course-hero__inner`: `nav.breadcrumb[aria-label=Trilha]` ("Cursos" / categoria), `h1.course-hero__title`, `p.course-hero__lead` (descrição), `div.row.gap-10` com `span.badge.badge--on-dark` para "Carga horária: Xh" (só se houver), "N módulos · N aulas · N min de vídeo" e "Certificado verificável".
- `div.container.course-body` > `div.split.split--32.split--reverse` (no celular o card de compra vem primeiro):
  - `div.split__main.split__main--600.gap-24`:
    - "O que você vai aprender": `section.card.card--pad-lg.stack.gap-16` com `h2.section-card__title` e `ul.check-list` (ícone `check` size 20 stroke 2.4). Só aparece se `course.objectives_list`.
    - "Conteúdo do curso": `section.card.card--clip.syllabus` com `div.syllabus__head` e, por módulo, `div.module` > `button.module__toggle[aria-expanded=true][aria-controls=prev-module-N]` (`span.module__title` + `span.text-14.muted` "2 aulas · 12 min") + `ul.module__list#prev-module-N` com `li.syllabus__item` (ícone `play-circle` 18, `span.syllabus__item-title`, `span.syllabus__item-meta`). O acordeão funciona com o mesmo código do `aluno.js`; nesta página, carregar `aluno.js` também.
    - "Para quem é este curso": só se `course.target_audience`.
    - "Perguntas frequentes": `div.faq-item` "Como recebo o certificado?" (fixo, texto na referência) e "Por quanto tempo tenho acesso?" só se `site.access_period_text`.
  - `aside.split__side.card.card--clip.buy-card`: `div.buy-card__cover` (img ou sigla), `div.buy-card__body`:
    - não matriculado: `span.buy-card__price`, `span.text-14.muted` "Pix ou cartão de crédito", `a.btn.btn--primary.btn--xl` "Comprar agora" para `checkout`, `ul.benefits` (N videoaulas, Material de apoio em PDF se `has_materials`, Certificado de Xh se houver carga, Dúvidas com os instrutores), `p.text-13.muted` "Já é aluno? Entre na sua conta.";
    - matriculado: sem preço, `a.btn.btn--primary.btn--xl` "Ir para o curso" para `next_lesson`.
- Remover: nota, classificações, número de alunos, "Mais vendido", "Criado por", "Última atualização", lista fixa de objetivos.

### 6.3 Checkout · `Checkout.dc.html`

- Rota existente. **Preserve** os `id` e `name` usados hoje: `checkout-main-form`, `credit-card-form-wrapper`, `pix-form-wrapper`, `payment_method_input`, `card_*_input`, `card_preview_*`, `base-course-price`, `summary-bumps-list`, `total-checkout-amount`, `selected_bumps_input`, `payment-loading-modal`, e os `name` lidos por `process_checkout`.
- Cabeçalho próprio: `{% block header %}` com `header.site-header` contendo só `a.brand` (sem tag) e `span.secure-note` (ícone `lock` 18 em `text-success`, "Pagamento seguro"). Sem rodapé (`{% block footer %}{% endblock %}`).
- `div.container.container--1180.split.split--32.split--reverse` com padding vertical de 40px (classe `course-body`):
  - `form#checkout-main-form.split__main.split__main--560`:
    - `section.card.card--pad-lg.stack.gap-18`: `div.step-head` (`span.step-num` 1, `h2.step-title.step-title--18` "Seus dados") + `div.form-grid` com nome completo (`span-all`, placeholder "Como deve sair no certificado"), e-mail (hint "O acesso ao curso chega neste e-mail."), CPF, celular. Campos que `process_checkout` não lê hoje: adicionar na view só se o gateway precisar; senão omitir.
    - `section.card.card--pad-lg.stack.gap-18`: passo 2 "Forma de pagamento", `div.radio-cards[role=radiogroup]` com `label.radio-card` para cartão e Pix (o JS atual alterna `#credit-card-form-wrapper` e `#pix-form-wrapper`; adapte os seletores de clique se necessário, mantendo os IDs), `div#credit-card-form-wrapper.form-grid.form-grid--160` com número (`span-all`), nome impresso (`span-all`), validade, CVV, parcelas.
    - Os elementos `card_preview_*` não aparecem no design novo. Se `checkout.js` escreve neles sem checar, acrescente checagem de `null` no JS em vez de recriar o visual.
    - Order bumps: fora do escopo do design. Se `order_bumps` vier vazio, não renderizar o bloco; manter `#summary-bumps-list` vazio e oculto no resumo.
  - `aside.split__side.card.card--pad-md.stack.gap-18`: "Resumo do pedido", `div.summary-product` (`span.course-tile.course-tile--64` + título + "Curso online · Xh"), `div.summary-lines` (Subtotal e `div.summary-line.summary-line--total` com `#total-checkout-amount`), `button.btn.btn--primary.btn--xl` "Finalizar compra", `p.text-13.muted` com termos e o aviso do e-mail.

### 6.4 Login · `Login.dc.html`

- `{% extends "base_core.html" %}`, `{% block body %}` com `div.auth`:
  - `section.auth__brand`: `a.auth__brand-link` (`span.auth__brand-name`, `span.auth__brand-tag`), `div.auth__pitch` (`h1.auth__title` "Sua área do aluno", `p.auth__lead`), `span.auth__foot` "Aprenda fazendo, com quem faz."
  - `main.auth__main` > `form.auth__form[method=post]`: `div.stack.gap-6` (`h2.auth__heading` "Entrar", `p.muted` "Use o e-mail cadastrado na compra."), alerta de erro (`alert alert--error`, texto "E-mail ou senha incorretos. Confira e tente de novo.") só quando houver erro, campo e-mail (`name="username"`, `type="email"`, `autocomplete="email"`), campo senha com `div.field__head` (rótulo + link "Esqueci minha senha" para `password_reset`), `input[type=hidden][name=next]`, `button.btn.btn--primary.btn--xl` "Entrar", `p.auth__switch` "Ainda não tem conta? Criar conta", `p.auth__note` com a orientação do primeiro acesso para quem veio da Eduzz ou Hotmart.
- Mensagens de `messages` (ex.: senha redefinida) aparecem acima do título com `partials/messages.html`.

### 6.5 Cadastro · `Cadastro.dc.html`

- Mesmo layout do login (`auth`), formulário `auth__form auth__form--420`. Título "Crie sua conta de aluno", heading "Criar conta", subtítulo "Leva menos de um minuto."
- Campos: nome completo (hint "É o nome que vai sair no certificado."), e-mail, senha (hint "Mínimo de 8 caracteres, sem ser só números."), confirmar senha, `label.check` com aceite (links para `site.terms_url` e `site.privacy_url`, obrigatório). Erros por campo com `aria-invalid` e `error-text`.
- Sem campo de tipo de perfil.

### 6.6 Esqueci minha senha · `EsqueciSenha.dc.html`

- `password_reset_form.html`: `div.auth-center` > `a.auth-center__brand` (`span.brand__name`, `span.brand__tag`) + `div.auth-center__stack` > `form.auth-card` ("Esqueci minha senha", texto, campo e-mail, `button.btn.btn--primary.btn--xl` "Enviar link", link "Voltar para o login").
- `password_reset_done.html`: mesma casca; no lugar do formulário, `div.alert.alert--success.alert--lg` (ícone `mail`) "Se este e-mail estiver cadastrado, você vai receber o link em alguns minutos. Confira também a caixa de spam." e o link para o login. Não confirmar se o e-mail existe.

### 6.7 Criar nova senha · `RedefinirSenha.dc.html`

- `password_reset_confirm.html`: `div.auth-center` > `form.auth-card`: título "Criar nova senha", texto "Também é aqui que você define a senha no primeiro acesso.", nova senha, confirmar, `ul.req-list[aria-label="Requisitos da senha"]` com três itens (ícone `check` quando ok com `li.is-ok`, ícone `circle` quando pendente), `button.btn.btn--primary.btn--xl` "Salvar e entrar".
- Os requisitos são informativos; a validação real é do Django. Atualizar `is-ok` em tempo real é opcional (se fizer, script inline proibido: crie `static/js/senha.js`).
- Link inválido ou expirado (`validlink` falso): `div.alert.alert--error` "Este link expirou ou já foi usado." + `a.btn.btn--primary` "Pedir um novo link".

### 6.8 Verificar certificado · `VerificarCertificado.dc.html`

- `base_public.html`, `{% block header_nav %}` com "Voltar ao site". Conteúdo em `div.container.container--720.section-block.section-block--56.gap-24`.
- `h1.page-title.page-title--32` + `p.muted`. `form[method=get].row.row--end.gap-12` com `div.field.grow` (`input.input.input--xl.input--code[name=codigo]`) e `button.btn.btn--primary.btn--xl` "Verificar".
- Resultado (só se `searched`): `section.card.card--clip` com `div.result-head` (ícone `check-circle` 24, `h2.result-head__title` "Certificado válido") e `dl.dl` (Aluno, Curso, Carga horária, Concluído em, Código com `|codigo_cert` em `mono`). Não encontrado: `div.result-head.result-head--invalid` com ícone `alert` e "Nenhum certificado encontrado com este código".
- `p.text-14.muted` "Por privacidade, esta página não mostra CPF nem outros dados pessoais do aluno."

### 6.9 Meus cursos · `Main.dc.html`

- Rota `/dashboard/` (nome `dashboard`). Contexto:
  - `continue_item`: matrícula não concluída com `last_accessed_at` mais recente (sem acesso ainda: a mais recente). Formato: `{course, pct, completed, total, next_lesson}`. `None` se não houver curso em andamento.
  - `my_courses`: lista de `{course, pct, completed, total, next_lesson, status}` (`status` = `not_started`, `in_progress` ou `done`).
  - `live_item`: primeiro curso matriculado com `live_meet_url`; `None` se nenhum.
  - `other_courses`: publicados em que o aluno não está matriculado.
- `{% block page_title %}Meus cursos{% endblock %}`. `{% block topbar_actions %}`: `a.user-chip` (avatar 32 + `span.user-chip__name` com o nome) + `form` de logout com `button.btn.btn--quiet` "Sair". `{% block page_class %}page--gap-40{% endblock %}`.
- Conteúdo, nesta ordem:
  1. `div.stack.gap-4`: `h2.page-title` "Olá, {{ primeiro nome }}" + `p.page-intro` "Você tem N cursos ativos. Continue de onde parou." (sem cursos: "Você ainda não tem cursos. Conheça os treinamentos abaixo.").
  2. Se `continue_item`: `section.card.continue[aria-labelledby=continuar]`: `div.continue__cover.{{ course.cover_class }}` (img ou `span.continue__initials`), `div.continue__body` com `span#continuar.eyebrow` "Continue de onde parou", `h2.continue__title`, `div.meta-row` (`span.meta-row__item` ícone `play` 16 "Próxima: Aula N · título" e `span.meta-row__item.meta-row__item--muted` ícone `clock` 16 duração), `div.progress-block.progress-block--w460` (progresso `size="lg"` + `span.progress-label` "25% concluído · 1 de 4 aulas"), `div.row.gap-12` com `a.btn.btn--primary.btn--lg` (ícone `play` 18) "Continuar aula" e `a.btn.btn--secondary.btn--lg` "Ver conteúdo do curso" (vai para `course_preview`).
  3. Se `live_item`: `section.card.live-strip`: `div.row.gap-16` (`span.icon-tile` ícone `video` 22 + `div.stack` com `h2.live-strip__title` "Aula ao vivo · curso" e `span.text-14.muted` "Próximo encontro na agenda") + `div.row.gap-12` com `a.btn.btn--ghost` "Ver agenda" (para `live_classes`) e `a.btn.btn--dark` "Entrar no Google Meet" (`target=_blank rel=noopener`).
  4. `section.section`: `div.section__head` (`h2.section__title` "Meus cursos" + `span.text-14.muted` "N cursos") + `div.course-grid` com `partials/course_card_owned.html`.
  5. Se `other_courses`: `section.section`: `div.stack.gap-4` (`h2.section__title` "Outros treinamentos CETREMER" + `span.text-14.muted` "Cursos que você ainda não tem. Veja o conteúdo antes de adquirir.") + `div.course-grid` com `{% include "partials/course_card_shop.html" with course=c locked=True cta="Conhecer curso" %}`.

### 6.10 Página da aula · `Aula.dc.html`

- Rota `/courses/<slug>/lessons/<id>/` (nome `lesson_detail`). Atualiza `Enrollment.last_accessed_at`. Contexto: `course`, `lesson`, `modules` (cada um com `lessons_list`, `done_count`, `total_count`), `completed_ids` (set), `completed_count`, `total`, `pct`, `total_seconds`, `prev_lesson`, `next_lesson_nav`, `lesson_index` (1 a N), `is_completed`, `materials`, `posts` (dúvidas desta aula, sem ocultos).
- Layout próprio: `{% extends "base_core.html" %}`, `{% block body %}` com `div.lesson-page`:
  - `header.lesson-topbar`: à esquerda `div.row.gap-12` com `a.back-link` (ícone `chevron-left` 18, "Meus cursos"), `span.divider-v[aria-hidden]`, `div.stack` (`span.lesson-topbar__brand` "CETREMER", `span.lesson-topbar__course`); à direita `div.row.gap-16` com `div.progress-inline` (barra com `data-course-progress` no `progress__bar` + `span.progress-label.nowrap` `<span data-progress-pct>25%</span> · <span data-progress-count>1 de 4</span>`) e `a.avatar` para `settings`.
  - `div.lesson-layout` > `main.lesson-main` e `aside.lesson-side[aria-label="Conteúdo do curso"]`.
- `main.lesson-main`, nesta ordem:
  1. Player:
     ```django
     <div class="player">
       {% if lesson.vimeo_id %}
       <iframe src="{{ lesson.player_url }}" data-vimeo data-lesson-id="{{ lesson.id }}"
               data-complete-url="{% url 'complete_lesson' lesson.id %}"
               allow="autoplay; fullscreen; picture-in-picture" allowfullscreen
               referrerpolicy="strict-origin-when-cross-origin" title="Vídeo da aula: {{ lesson.title }}"></iframe>
       {% elif lesson.youtube_embed_url %}
       <iframe src="{{ lesson.youtube_embed_url }}" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" title="Vídeo da aula: {{ lesson.title }}"></iframe>
       {% else %}
       <div class="player__empty">Vídeo ainda não disponível.</div>
       {% endif %}
     </div>
     ```
  2. `div.lesson-head`: `div.stack.gap-4` (`span.text-13.muted` "Módulo N · título · Aula X de N", `h1.lesson-head__title`) e o botão:
     ```django
     {% csrf_token %}
     <button type="button" class="btn btn--lg btn-toggle-complete {% if is_completed %}btn--done{% else %}btn--primary{% endif %}"
             data-lesson-id="{{ lesson.id }}" data-url="{% url 'toggle_progress' lesson.id %}" aria-pressed="{{ is_completed|yesno:'true,false' }}">
       {% include "partials/icon.html" with name="check" size=18 stroke="2.4" %}
       <span data-label>{% if is_completed %}Concluída{% else %}Marcar como concluída{% endif %}</span>
     </button>
     <p class="error-text" data-progress-error hidden>Não foi possível salvar. Tente de novo.</p>
     ```
  3. `nav.lesson-nav[aria-label="Navegação entre aulas"]`: `a.lesson-nav__link` anterior (ícone `chevron-left`, `span.lesson-nav__text` com `span.lesson-nav__label` "Aula anterior" e `span.lesson-nav__title`) e `a.lesson-nav__link.lesson-nav__link--next` próxima (texto + `chevron-right`). Omitir o que for `None`.
  4. `section.card.card--pad.stack.gap-10` "Sobre esta aula" (`h2.card__title`, `p.text-2` com `lesson.description|linebreaksbr`). Omitir se vazio.
  5. `section.card.card--pad.stack.gap-14` "Material de apoio" com um `a.file-item` por material (`span.icon-tile.icon-tile--40` ícone `file`, `span.file-item__text` com `span.file-item__name` e `span.file-item__meta` "PDF · abre em nova aba", ícone `download` 18 `muted`), `target=_blank rel=noopener`. Omitir se não houver.
  6. `section.card.card--pad.stack.gap-14` "Dúvidas sobre esta aula": subtítulo "Sua pergunta vai para o fórum do curso, e os instrutores respondem por lá.", formulário (POST para a rota de criar post com `course_id` e `lesson_id` ocultos, `label.field__label` "Sua dúvida", `textarea.textarea`, `button.btn.btn--outline.self-end` "Publicar dúvida"), lista de `article.post` (seção 6.14) ou `p.empty.empty--sm` "Ninguém perguntou nada nesta aula ainda."
- `aside.lesson-side`:
  1. `div.card.card--clip`: `div.curriculum__head` (`h2.curriculum__title` "Conteúdo do curso", barra com `data-course-progress`, `span.progress-label` `<span data-progress-count>1 de 4</span> aulas concluídas · {{ total_seconds|duracao }} no total`) e um `div.module` por módulo:
     ```django
     <div class="module">
       <button type="button" class="module__toggle module-title-btn" aria-expanded="true" aria-controls="module-{{ m.id }}">
         <span class="module__text">
           <span class="module__title">Módulo {{ forloop.counter }} · {{ m.title }}</span>
           <span class="module__count" data-module-count="{{ m.id }}">{{ m.done_count }} de {{ m.total_count }} aula{{ m.total_count|pluralize }}</span>
         </span>
         {% include "partials/icon.html" with name="chevron-up" size=18 class="module__chevron module-toggle-icon" %}
       </button>
       <ul class="module__list" id="module-{{ m.id }}">
         {% for l in m.lessons_list %}
         <li>
           <a class="lesson-item" href="{% url 'lesson_detail' course.slug l.id %}"{% if l.id == lesson.id %} aria-current="page"{% endif %}>
             <span class="status-dot{% if l.id in completed_ids %} is-done{% endif %}{% if l.id == lesson.id %} is-current{% endif %}" id="status-dot-{{ l.id }}" aria-hidden="true">
               {% include "partials/icon.html" with name="check" size=13 stroke="3" class="icon--check" %}
               {% include "partials/icon.html" with name="play" size=11 class="icon--play" %}
             </span>
             <span class="lesson-item__text">
               <span class="lesson-item__title">{{ l.position }}. {{ l.title }}</span>
               <span class="lesson-item__meta" data-lesson-meta="{{ l.id }}" data-duration="{{ l.duration_seconds|duracao }}">
                 {% if l.id == lesson.id %}Assistindo agora · {{ l.duration_seconds|duracao }}{% elif l.id in completed_ids %}Concluída · {{ l.duration_seconds|duracao }}{% else %}{{ l.duration_seconds|duracao }}{% endif %}
               </span>
             </span>
           </a>
         </li>
         {% endfor %}
       </ul>
     </div>
     ```
     `l.position` é a numeração contínua no curso (1 a N, não reinicia por módulo), atribuída na view percorrendo a ordem da seção 4.5. O mesmo número entra em "Aula X de N" e no badge "BLS · Aula 2" da comunidade (`lesson_position`).
     O módulo da aula atual começa aberto; os demais também (todos abertos, como no design).
  2. `div.card.status-card`: `span.icon-tile.icon-tile--40.icon-tile--neutral` ícone `award`, `span.stack` com "Certificado" (`fw-600 text-14`) e `span.text-13.muted` "Liberado ao concluir 100% das aulas. Faltam N." ou, se 100%, link "Ver certificado".
- Classes `module-title-btn` e `module-toggle-icon` ficam por compatibilidade, mas não há mais CSS nem JS antigo nelas.

### 6.11 Aulas ao vivo · `AoVivo.dc.html`

- Rota nova `/ao-vivo/` (nome `live_classes`). Contexto: `live_courses` (matriculados com `live_meet_url` ou `live_calendar_url`), `other_enrolled` (matriculados sem nenhum dos dois).
- `p.page-intro.page-intro--max` "Encontros ao vivo dos cursos em que você está matriculado. O link do Google Meet abre na hora marcada."
- Por curso ao vivo, um `section.card.card--clip`:
  1. `div.card--pad.row.row--between.gap-16`: à esquerda `div.row.gap-16` com `span.course-tile.course-tile--56.{{ c.cover_class }}` e `div.stack` (`h2.card__title.card__title--lg` com o nome do curso + `span.text-14.muted` "Encontros ao vivo deste curso"); à direita `a.btn.btn--primary.btn--lg` com ícone `video` 18 "Entrar no Google Meet" (só se `live_meet_url`, `target=_blank rel=noopener`).
  2. Se `calendar_embed_url`: `div.card__divider` e depois `div.card--pad.stack.gap-12` com `h3.text-15.fw-600` "Agenda", `<iframe class="calendar-embed" src="{{ c.calendar_embed_url }}" title="Agenda de aulas ao vivo de {{ c.title }}" loading="lazy"></iframe>` e `a.link-strong.text-14.self-start` "Adicionar ao meu Google Agenda" (para `live_calendar_url`, nova aba).
- Cursos sem encontro: `section.card.card--dashed.status-card` com tile e "Este curso não tem encontros ao vivo agendados."
- Nenhum curso ao vivo: `div.empty` "Nenhum dos seus cursos tem aulas ao vivo no momento."

### 6.12 Certificados · `Certificados.dc.html`

- Contexto da seção 4.6. Se faltar nome ou CPF: `div.alert.alert--warning.alert--banner` com o aviso e o link "Completar dados".
- `div.course-grid.course-grid--320` e um `article.card.card--pad-md.stack.gap-14` por curso: cabeçalho (`div.row.gap-14` com `span.course-tile.{{ c.cover_class }}` + `div.stack` com `h2.course-card__title` e `span.text-13.muted` "Carga horária: Xh"), e:
  - não emitido: progresso + `span.progress-label` ("Em andamento · faltam N aulas" ou "Não iniciado · N aulas") + `a.btn.btn--secondary.btn--block` "Ver requisitos" (vai para `issue_certificate`, que mostra a tela bloqueada);
  - emitido: classe extra `card--success`, `span.post__answered` (ícone `check-circle` 18) "Emitido em dd/mm/aaaa", `div.row.gap-10` com `a.btn.btn--primary.grow` "Ver certificado" e `a.btn.btn--secondary.grow` "Baixar PDF". O "Baixar PDF" aponta para a URL do certificado com `?imprimir=1`; o `site.js` abre a impressão ao carregar quando vê esse parâmetro.
- O card "Exemplo: curso concluído" da referência é só ilustrativo do estado emitido. Não renderizar exemplo.

### 6.13 Certificado emitido e bloqueado · `Certificado.dc.html`, `CertificadoBloqueado.dc.html`

- `certificate.html`: `{% extends "base_core.html" %}`, `div.cert-page` > `header.lesson-topbar.no-print` (`a.back-link` "Meus certificados" para `certificates`; à direita `button.btn.btn--secondary[data-copy="{{ verify_url }}"]` ícone `link` com `span[data-label]` "Copiar link de verificação" e `button.btn.btn--primary[data-print]` ícone `download` "Baixar PDF") + `main.cert-wrap` > `article.certificate[aria-label=Certificado]` > `div.certificate__frame`:
  marca (`img.certificate__logo` se `site.logo`, senão `span.certificate__brand-name` + `span.certificate__brand-tag`), `h1.certificate__title` "CERTIFICADO" (texto exigido pelo teste), `p.certificate__intro` "Certificamos que", `p.certificate__name` = `certificate.student_name`, `p.certificate__text` "portador(a) do CPF {{ certificate.student_cpf|cpf }}, concluiu o curso <strong>{{ certificate.course_title }}</strong>, com carga horária de <strong>{{ certificate.workload_hours }} horas</strong>, em {{ certificate.completed_at|date:'d/m/Y' }}." (sem carga: omitir o trecho), `div.certificate__footer` com `div.certificate__code` ("Código de verificação", `span.certificate__code-value` `|codigo_cert`, "Confira em {{ request.get_host }}/certificado/verificar") e `div.signature` (`img.signature__img` se houver, `span.signature__line`, `span.signature__name` = `site.signer_name`, `span.signature__role` = `site.signer_role`).
- `certificate_error.html`: `div.lesson-page` com `header.lesson-topbar` (`a.back-link` "Meus certificados" + `span.lesson-topbar__brand` "CETREMER") e `main.center-page` > `section.center-page__card.card.card--pad-xl.stack.gap-22`: `span.icon-tile.icon-tile--56.icon-tile--neutral` ícone `lock` 26, `h1.auth-card__title` "Certificado Bloqueado" (texto exigido pelo teste), texto, `ul.list-plain.stack.gap-12` com dois `li.req-item` (`is-ok` quando cumprido; marca com ícone `check`): "Concluir 100% das aulas" (progresso + "1 de 4 aulas · faltam 3") e "Informar nome completo e CPF" (link "Completar em Minha conta"), `a.btn.btn--primary.btn--xl` "Continuar o curso" para `next_lesson`.

### 6.14 Comunidade · `Comunidade.dc.html`

- Rota existente `/community/`. Contexto: `posts` (sem ocultos, só de cursos matriculados e gerais), `my_courses`, `current_filter`.
- `div.split` > `main.split__main.split__main--480.gap-16` e `aside.split__side.split__side--320.card.card--pad-md.stack.gap-14`.
- Filtros: `div.chips` com `a.chip` (links `?curso=geral`, `?curso=<slug>`) e `aria-current="page"` no ativo.
- Post:
  ```django
  <article class="card post">
    <div class="post__meta">
      <span class="avatar avatar--32 avatar--soft" aria-hidden="true">{{ p.author_display|iniciais }}</span>
      <span class="post__author">{{ p.author_display }}</span>
      <span>· {{ p.created_at|timesince }} atrás</span>
      <span class="badge {% if p.course %}{{ p.course.category.badge_class|default:'badge--blue' }}{% else %}badge--gray{% endif %}">{% if p.course %}{{ p.course.short_name|default:p.course.title }}{% if p.lesson %} · Aula {{ p.lesson_position }}{% endif %}{% else %}Discussão geral{% endif %}</span>
    </div>
    <h2 class="post__title"><a href="...">{{ p.title }}</a></h2>
    <p class="post__excerpt">{{ p.content }}</p>
    <div class="post__foot">
      {% if p.is_answered %}<span class="post__answered">{% include "partials/icon.html" with name="check" size=16 stroke="2.4" %}Respondida pelo instrutor</span>{% endif %}
      <span class="muted">{{ p.comments_count }} resposta{{ p.comments_count|pluralize }}</span>
    </div>
  </article>
  ```
  `author_display` = nome completo ou parte do e-mail antes do @; nunca o e-mail inteiro.
- Formulário lateral "Nova pergunta": select "Sobre" só com "Discussão geral" e os cursos matriculados (hint "Só aparecem os cursos em que você está matriculado."), título, detalhes, `button.btn.btn--primary.btn--lg` "Publicar".
- Vazio: `div.empty` "Ainda não há perguntas por aqui. Seja o primeiro a perguntar."

### 6.15 Minha conta · `MinhaConta.dc.html`

- Rota existente `/settings/`. Manter os `action` atuais (`profile_account`, `profile_personal`, troca de senha) e remover o formulário de endereço.
- `{% block page_class %}page--w880 page--gap-24{% endblock %}`. Topo com `form` de logout (`button.btn.btn--quiet` "Sair").
- Quatro `section.card.card--pad-lg.stack.gap-18`:
  1. "Dados de acesso": `div.row.gap-16` (avatar 64 + `button.btn.btn--secondary` "Trocar foto" que aciona `input[type=file].sr-only`), campo e-mail em `div.field.field--narrow`, `button.btn.btn--primary.self-start` "Salvar".
  2. "Dados para o certificado" com subtítulo, `div.form-grid` nome completo + CPF (`|cpf` no `value`; erro com `aria-invalid` e `error-text` "CPF inválido. Confira os números."), "Salvar".
  3. "Senha": `div.form-grid.form-grid--200` com atual, nova, confirmar; `button.btn.btn--outline.self-start` "Atualizar senha".
  4. "Meus pedidos": `div.table-wrap.table-wrap--bare` > `table.table.table--plain.table--w520` (Data, Curso, Valor `|brl`, Status com `badge badge--md`). Vazio: `div.empty.empty--sm` "Você ainda não tem pedidos."
- Sucesso de qualquer formulário: `messages.success("Dados salvos com sucesso.")`.

### 6.16 Painel · `AdminPainel.dc.html`

- Contexto: `month_revenue` (soma de pedidos `COMPLETED` no mês), `month_paid_count`, `students_count` (usuários com ao menos uma matrícula), `active_enrollments`, `courses_with_enrollments`, `pending_questions`, `recent_enrollments` (5), `recent_orders` (5).
- `{% block page_title %}Painel{% endblock %}`; topo com `span.text-14.text-2` "Administrador" (nome do usuário).
- `div.row.gap-12` ações: "Novo curso" (`btn--primary`), "Matricular aluno" e "Importar alunos" (`btn--secondary`).
- `div.metric-grid` com 4 `div.metric`: "Vendas no mês" (`|brl`, foot "N pedidos pagos"), "Alunos" (foot "com pelo menos 1 curso"), "Matrículas ativas" (foot "em N cursos"), "Dúvidas sem resposta" (foot com link "Ver comunidade").
- `div.split` com dois `section.split__half.card.card--pad-md.stack.gap-12`: "Matrículas recentes" (`ul.list-plain` com `li.list-row`) e "Últimos pedidos" (mesma lista; vazio: `p.empty` "Nenhum pedido ainda. Os pedidos aparecem aqui assim que o gateway estiver ativo.").

### 6.17 Cursos (admin) · `AdminCursos.dc.html`

- `topbar_actions`: `a.btn.btn--primary` "Novo curso". `div.toolbar` (busca + select de categoria, com `label.sr-only`, form GET).
- `div.table-wrap` > `table.table.table--w860`: Curso (`div.cell-media` com `span.course-tile.course-tile--thumb.{{ c.cover_class }}` + `span.fw-600`), Categoria, Preço (`|brl`), Aulas, Alunos, Status (`badge badge--md badge--success` "Publicado" ou `badge--gray` "Rascunho"), ações (`a.link-strong` "Editar" · "Aulas"). Cabeçalho da coluna de ações com `span.sr-only` "Ações".

### 6.18 Editar curso · `AdminCursoEditar.dc.html`

- `topbar_class` = `topbar--compact`; `topbar_eyebrow` = `a.topbar__eyebrow` "Cursos"; título = nome do curso (ou "Novo curso"); ações: "Aulas do curso" e "Ver página de venda" (`btn--secondary`, só ao editar) e `button.btn.btn--primary[form=course-form]` "Salvar alterações".
- `form#course-form[enctype=multipart/form-data].split` > `div.split__main.gap-20` com três `section.card.card--pad.stack.gap-16` ("Informações do curso": título; `form-grid--180` com categoria, carga horária em horas, preço; descrição) ("Página de venda": `fieldset.fieldset[data-repeater]` com legenda "O que você vai aprender", `div[data-repeater-list]` de `div.row.gap-8[data-repeater-item]` (input `name="objectives"` + `button.icon-btn[data-repeater-remove][aria-label="Remover objetivo"]` ícone `x`), `button.btn.btn--dashed.btn--sm.self-start[data-repeater-add]` "Adicionar objetivo", `<template data-repeater-template>` com um item vazio; "Para quem é" textarea) ("Aulas ao vivo": link do Meet; link da agenda com hint "Cole o link público da agenda. A plataforma monta a visualização sozinha.") + `div.split__side.split__side--300.gap-20` com "Publicação" (`label.toggle-row`), "Capa" (prévia `div.course-card__cover` com a capa atual ou sigla, hint "Proporção 3:2, mínimo de 1200 × 800 px.", `label.btn.btn--secondary` "Trocar imagem" com `input[type=file].sr-only`) e "Resumo" (linhas `div.summary-line.text-14` Módulos, Aulas, Tempo de vídeo, Alunos matriculados). Campos sigla (`short_name`) e cor da capa (`cover_color`) entram no card "Capa".
- Na view, `objectives` (lista) vira `learning_objectives` juntando com `\n`.

### 6.19 Aulas do curso · `AdminGrade.dc.html`

- Rota `painel:course_lessons`. Contexto: `course`, `modules` (com aulas e `material_count`), `selected_lesson` (de `?aula=`), `new_lesson_module` (de `?nova=`), `lesson_form`.
- Topo: eyebrow com links "Cursos / BLS", título "Aulas do curso", `button.btn.btn--primary[data-dialog-open=novo-modulo]` "Novo módulo" (diálogo com título do módulo).
- `div.split` > `div.split__main.split__main--460.gap-16[data-reorder-url="{% url 'painel:course_reorder' course.id %}"]` e `section.split__side.split__side--380.card.card--pad.stack.gap-16`.
- Módulo:
  ```django
  <section class="card card--clip" data-module-id="{{ m.id }}" draggable="true" aria-labelledby="m{{ m.id }}">
    <div class="builder-module__head">
      <button type="button" class="drag-handle" aria-label="Mover módulo {{ m.title }}">{% include "partials/icon.html" with name="drag" size=16 %}</button>
      <h2 id="m{{ m.id }}" class="builder-module__title">Módulo {{ forloop.counter }} · {{ m.title }}</h2>
      <button type="button" class="btn btn--secondary btn--sm" data-dialog-open="renomear-{{ m.id }}">Renomear</button>
    </div>
    <ul class="module__list" data-module-id="{{ m.id }}">
      {% for l in m.lessons_list %}
      <li class="builder-lesson{% if selected_lesson.id == l.id %} is-editing{% endif %}" data-lesson-id="{{ l.id }}" draggable="true">
        <button type="button" class="drag-handle" aria-label="Mover aula {{ l.title }}">{% include "partials/icon.html" with name="drag" size=16 %}</button>
        <span class="builder-lesson__text">
          <span class="builder-lesson__title">{{ l.title }}</span>
          {% if selected_lesson.id == l.id %}<span class="builder-lesson__meta">Editando agora</span>
          {% elif not l.video_url %}<span class="builder-lesson__meta builder-lesson__meta--warn">Sem vídeo</span>
          {% else %}<span class="builder-lesson__meta">Vimeo · {{ l.duration_seconds|duracao }}{% if l.material_count %} · {{ l.material_count }} materia{{ l.material_count|pluralize:"l,is" }}{% endif %}</span>{% endif %}
        </span>
        {% if selected_lesson.id != l.id %}<a class="btn btn--secondary btn--sm" href="?aula={{ l.id }}">Editar</a>{% endif %}
      </li>
      {% endfor %}
    </ul>
    <a class="builder-add" href="?nova={{ m.id }}">Adicionar aula</a>
  </section>
  ```
  O `builder-add` como `<a>` já está coberto no CSS (seção 25b).
- Painel lateral "Editar aula" (ou "Nova aula"): título, link do Vimeo (hint de sucesso `text-success` com ícone `check` "Vídeo encontrado · duração 7:00 lida automaticamente" após salvar; erro como na seção 4.4), descrição, "Materiais de apoio" (lista dos existentes com `a.file-item` e remover + `label.dropzone[data-dropzone]` "Arraste arquivos ou escolha no computador", hint "PDF, até 20 MB por arquivo"), `div.form-actions` com `button.btn.btn--danger-text[name=action][value=delete_lesson]` "Excluir aula" (com `<dialog>` de confirmação, nunca `confirm()`) e `button.btn.btn--primary` "Salvar aula". Sem aula selecionada: `div.empty` "Escolha uma aula para editar ou adicione uma nova."
- Excluir aula com alunos que concluíram: o diálogo avisa "N alunos já concluíram esta aula. O progresso deles nela será apagado."

### 6.20 Reordenação

- `course_reorder` recebe o JSON do `painel-grade.js`, valida que todos os IDs pertencem ao curso, grava `Module.order` (1..n), `Lesson.module` e `Lesson.order` (1..n dentro de cada módulo) numa transação e responde `{"ok": true}`. Como a URL da aula agora usa `lesson.id`, reordenar não quebra nenhum link.

### 6.21 Alunos · `AdminAlunos.dc.html`

- Contexto: `students` (paginado de 25 em 25, com `courses_count` e `first_enrollment_source`), `selected` (de `?aluno=`) com `enrollments` (curso, done, total, pct) e `available_courses`.
- Topo: `a.btn.btn--secondary` "Importar alunos" e `button.btn.btn--primary[data-dialog-open=matricular]` "Matricular aluno".
- `div.split` > `div.split__main.gap-16` (toolbar com busca "Buscar por nome, e-mail ou CPF", select de curso, `a.btn.btn--secondary` "Exportar CSV"; `div.table-wrap` > `table.table.table--w640`: Aluno (`div.cell-stack` com `a.cell-title` para `?aluno=` + e-mail `muted`), Cursos, Origem (rótulo de `Enrollment.source`), Cadastro (`date_joined|date:"d/m/Y"`); linha do selecionado com `tr.is-selected`; paginação com `a.btn.btn--secondary.btn--sm`).
- `section.split__side.card.card--pad.stack.gap-16` (só com `selected`): avatar 52 + nome + e-mail, `dl.dl.dl--compact` (Nome completo e CPF; ausente em `text-danger` "Não informado"), "Cursos" com um `div.card--inner.stack.gap-6` por matrícula com progresso e `button.btn--link-danger[name=action][value=unenroll]` "Remover acesso" (com diálogo de confirmação), "Liberar outro curso" (`div.row.gap-8` com select + `button.btn.btn--primary` "Liberar"), `button.btn.btn--secondary.btn--block[name=action][value=resend_access]` "Reenviar e-mail de acesso".
- `<dialog class="dialog" id="matricular">` > `form.dialog__body`: `h2.dialog__title` "Matricular aluno", e-mail, nome completo, curso, `label.check` "Enviar e-mail de acesso agora" (marcado), `div.dialog__actions` com "Cancelar" (`btn--secondary`, `data-dialog-close`) e "Matricular" (`btn--primary`).

### 6.22 Importar alunos · `AdminImportar.dc.html`

- `{% block page_class %}page--w980 page--gap-20{% endblock %}`, eyebrow "Alunos", título "Importar alunos".
- Três `section.card.card--pad.stack.gap-12` com `div.step-head` (`step-num` 1, 2, 3):
  1. "Prepare a planilha": texto com as colunas aceitas, `a.btn.btn--secondary.self-start` "Baixar modelo CSV" (arquivo estático `static/modelos/importar-alunos.csv` com cabeçalho `nome,email,cpf`).
  2. "Escolha os cursos e envie o arquivo": `fieldset.fieldset` com legenda "Liberar acesso a" e `div.checks-inline` de `label.check.check--inline`, `label.dropzone.dropzone--lg[data-dropzone]` com input `.csv` e `span[data-dropzone-name]`, `button.btn.btn--primary` "Ler arquivo".
  3. Só depois da leitura: "Confira antes de importar": `div.row.gap-10` com `span.badge.badge--lg.badge--success` "N novos", `badge--blue` "N já cadastrados, ganham o curso", `badge--danger` "N com erro, serão ignorados"; `div.table-wrap.table-wrap--flat` > `table.table.table--compact.table--w560` (Nome, E-mail, Situação com `fw-600` e `text-success`, `text-primary` ou `text-danger`), mostrando as 50 primeiras linhas e "e mais N linhas"; `label.check` "Enviar e-mail de acesso agora" com hint; `button.btn.btn--primary.btn--lg.self-start[name=action][value=confirm]` "Importar alunos".

### 6.23 Pedidos · `AdminPedidos.dc.html`

- `metric-grid` com 3 `metric.metric--sm`: "Pagos no período" (`|brl`), "Aguardando pagamento", "Recusados".
- `form.toolbar` GET: busca, status (Todos, Pago, Aguardando, Recusado, Reembolsado), período (Últimos 30 dias, Este mês, Mês passado). "Personalizado" fica fora desta versão.
- `table.table.table--w780`: Data (`d/m · H:i`), Aluno (`cell-stack`), Curso (sigla), Forma ("Pix" ou "Cartão · Nx"), Valor (`td.num`), Status (`badge badge--md`). Paginação de 25.
- Vazio: `div.empty` "Nenhum pedido no período." A nota "Linhas de exemplo" da referência não vai para a tela.

### 6.24 Comunidade (admin) · `AdminComunidade.dc.html`

- Abas com `div.chips[role=tablist]` de `a.chip` e `aria-current="page"` na ativa: "Sem resposta (N)", "Respondidos", "Ocultos".
- `article.card.post.post--admin` com meta (autor, tempo, badge "BLS · Aula 2"), `h2.post__title`, texto completo, respostas existentes, `div.field` "Responder como CETREMER" (`textarea`), `div.row.row--between.gap-10` com `button.btn.btn--secondary[name=action][value=hide]` "Ocultar tópico" (em Ocultos: "Mostrar tópico") e `button.btn.btn--primary[name=action][value=reply]` "Publicar resposta".
- Vazio em "Sem resposta": `p.empty.empty--dashed` "Tudo respondido."

### 6.25 Configurações · `AdminConfiguracoes.dc.html`

- `{% block page_class %}page--w920 page--gap-20{% endblock %}`. Um único `form[enctype=multipart/form-data]` com quatro `section.card.card--pad.stack.gap-16` e, no fim, `div.row.row--end` com `button.btn.btn--primary.btn--lg` "Salvar configurações".
  1. "Dados da escola": `form-grid` (nome exibido, WhatsApp de suporte), logo (`span.upload-preview.upload-preview--logo` + `label.btn.btn--secondary` "Enviar logo"), links de Termos e Privacidade.
  2. "Pagamentos": cabeçalho `div.row.row--between` com `span.badge.badge--md.badge--warning` "Modo de teste" quando `gateway_sandbox`. `form-grid` com select de gateway (só as opções implementadas) e a chave:
     ```django
     <div class="field" data-secret>
       <span class="field__label" id="lbl-chave">Chave da API</span>
       <div class="secret-field" data-secret-display>
         {% if gateway_key_last4 %}<span class="secret-field__value">Salva · termina em ••••{{ gateway_key_last4 }}</span>
         {% else %}<span class="secret-field__empty">Nenhuma chave salva</span>{% endif %}
         <button type="button" class="btn btn--secondary btn--xs" data-secret-replace>{% if gateway_key_last4 %}Substituir{% else %}Definir{% endif %}</button>
       </div>
       <input class="input" type="password" name="gateway_key" autocomplete="off" aria-labelledby="lbl-chave" data-secret-input hidden>
     </div>
     ```
     `label.toggle-row` "Usar ambiente de testes" e `p.hint` "Por segurança, chaves salvas nunca aparecem completas. Para trocar, use Substituir."
  3. "E-mails da plataforma": `form-grid--200` (nome do remetente, e-mail de envio, servidor SMTP, porta, usuário), senha no mesmo padrão `data-secret` (`email_password_set`), `button.btn.btn--secondary.self-start[name=action][value=test_email]` "Enviar e-mail de teste" (envia para o e-mail do usuário logado e mostra sucesso ou o erro do SMTP).
  4. "Certificado": cabeçalho com link "Ver modelo"; `form-grid` (responsável técnico; cargo e registro com placeholder "Ex.: Médico · CRM-MS 00000"); `span.upload-preview.upload-preview--signature` + `label.btn.btn--secondary` "Enviar imagem da assinatura".

---

## 7. Ordem de implementação

Cada fase termina com `python manage.py test` verde, conferência visual nas larguras 375, 768 e 1280 px e um commit.

| Fase | Entrega | Critério de aceite |
| --- | --- | --- |
| 0 | Copiar kit: CSS, JS, bases, partials, templatetags, validators. Context processor `site`. Criar desde já as rotas citadas pelos layouts novos, mesmo com view provisória que renderiza "Em construção" dentro do layout: `live_classes`, `certificates`, `verify_certificate`, `complete_lesson`, `password_reset` e o namespace `painel` com `dashboard`, `courses`, `students`, `orders`, `community`, `settings`. Sem isso, `{% url %}` nos menus quebra a página. | Todas as páginas atuais ainda abrem. |
| 1 | Modelos e migrations da seção 4.1, seed atualizado, `SiteSettings`, `cryptography` e `FIELD_ENCRYPTION_KEY`. | `migrate` limpo do zero e `loaddata` funcionando. |
| 2 | Login por e-mail, cadastro, recuperar senha, backend de e-mail. Telas 6.4 a 6.7. | Fluxo completo de "Esqueci minha senha" com e-mail no console. |
| 3 | Área do aluno: 6.9, 6.10 (com Vimeo), 6.11, 6.14, 6.15. Remover pontos e nível. | Concluir aula pelo botão e pelo fim do vídeo atualiza barra, contador do módulo e bolinha sem recarregar. |
| 4 | Certificado: 4.6, telas 6.12, 6.13, 6.8. | Aluno sem CPF vê "Certificado Bloqueado" com o requisito; com tudo ok, emite, imprime em A4 paisagem e o código verifica na página pública. |
| 5 | Público: 6.1, 6.2, 6.3. | Teste "Custom Banner Title" passa; checkout continua funcionando com o `checkout.js`. |
| 6 | Painel: 4.2, 4.7 a 4.10, telas 6.16 a 6.25, redirecionamentos de `/creator/`. | Importar um CSV de teste com 3 linhas (nova, existente, inválida) dá o resultado esperado; nenhuma chave aparece no HTML (conferir com "ver código-fonte"). |
| 7 | Limpeza: remover `main.css`, `components.css`, `netflix.js`, templates `creator/`, emojis, `|safe` indevidos, link fixo para `/admin/` no dashboard. | `grep -rn 'style="' templates/` só encontra o `partials/progress.html`. `grep -rnP '[\x{1F300}-\x{1FAFF}]' templates/` vazio. |

---

## 8. Checklist final (copiar no PR)

- [ ] Só `cetremer.css` carregado; nenhum `<style>` e nenhum `style=""` além da barra de progresso.
- [ ] Nenhuma cor hexadecimal fora de `:root`.
- [ ] Todas as telas da tabela da seção 0 implementadas e conferidas lado a lado com a referência.
- [ ] Nenhum emoji, nenhuma prova social inventada, nenhum "TheMembers", nenhum "Desenvolvido com Python e Django".
- [ ] Dinheiro com `|brl` em todo lugar.
- [ ] Um `<h1>` por página; todos os campos com rótulo; botões só com ícone com `aria-label`.
- [ ] Testado em 375, 768 e 1280 px sem rolagem horizontal da página (tabelas rolam dentro de `table-wrap`).
- [ ] Login por e-mail, recuperar senha e primeiro acesso funcionando.
- [ ] Aula: botão e fim do vídeo concluem; anterior e próxima corretas; aula inexistente dá 404.
- [ ] Certificado só com 100% e dados completos; verificação pública sem CPF.
- [ ] Painel acessível só por staff, ADMIN ou CREATOR; `/creator/` redireciona.
- [ ] Segredos criptografados, nunca no HTML; `.env` e `db.sqlite3` fora do git.
- [ ] Nenhum `|safe` em conteúdo de usuário.
- [ ] `python manage.py test` verde.

---

## 9. Fora de escopo nesta entrega

- Tema escuro (os tokens já estão prontos para isso).
- Tutor de IA e order bumps (ficam no banco, sem interface).
- Gateways além do escolhido pela cliente.
- Período personalizado no filtro de pedidos.
- Deploy (WhiteNoise, Docker, banco de produção).

## 10. Dados que ainda dependem da cliente

| Dado | Onde aparece | Enquanto não vier |
| --- | --- | --- |
| Carga horária do Plantão Sem GPT | cards, venda, certificado | campo vazio, trecho omitido |
| Números da landing (+2.000 alunos etc.) | landing | manter os do site atual |
| Domínio de produção | certificado, Vimeo | usar `request.get_host` |
| Gateway escolhido | configurações, checkout | manter o MOCK |
| Prazo de acesso aos cursos | FAQ da venda | pergunta omitida |
| Responsável técnico e assinatura | certificado | campos vazios, linha de assinatura sem nome |
| Logo em arquivo | todas as telas, certificado | marca em texto |
| Exportação real da Eduzz e da Hotmart | importação | aliases da seção 4.10 |
