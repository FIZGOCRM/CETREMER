from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from core.decorators import painel_required
from users.models import SiteSettings,EmailLog
from users.services import save_site_configuration,send_configuration_test
from users.notifications import pending_email_count
from painel.settings_forms import SECTIONS,SiteConfigurationForm
from .common import page

@painel_required
def settings(request):
    tab=request.GET.get('aba','membros')
    if tab not in (*SECTIONS,'ajuda','avisos'):tab='membros'
    site=SiteSettings.load()
    section=tab if request.method!='POST' or request.POST.get('section') else None
    form=SiteConfigurationForm(request.POST or None,request.FILES or None,instance=site,section=section)
    if request.method=='POST' and form.is_valid():
        try:save_site_configuration(form.save(commit=False),actor=request.user,email_password=form.cleaned_data.get('email_password',''))
        except ValidationError as exc:form.add_error(None,' '.join(exc.messages))
        else:
            if request.POST.get('action')=='test_email':
                if send_configuration_test(request.user):messages.success(request,'E-mail de teste aceito pelo servidor. Confira o recebimento na sua caixa de entrada.')
                else:messages.error(request,'E-mail de teste não foi enviado. Confira SMTP, remetente e registro de envio.')
            else:messages.success(request,'Configurações salvas.')
            return redirect(reverse('painel:settings')+'?aba='+tab)
    return page(request,'settings',form=form,tab=tab,email_password_set=bool(site.email_password_encrypted),pending_email_count=pending_email_count(),email_logs=EmailLog.objects.select_related('user').order_by('-created_at')[:30])
