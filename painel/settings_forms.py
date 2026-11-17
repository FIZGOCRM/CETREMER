from django import forms
from users.models import SiteSettings

SECTIONS={
 'membros':['school_name','logo','support_email','whatsapp','terms_url','privacy_url'],
 'mentoria':['mentor_display_name','mentor_label','team_display_name'],
 'plano':['access_period_text'],
 'certificado':['signer_name','signer_role','signature_image'],
 'email':['email_from_name','email_from','email_host','email_port','email_username','email_password','email_use_tls'],
}
class SiteConfigurationForm(forms.ModelForm):
 email_password=forms.CharField(required=False,label='Nova senha SMTP',widget=forms.PasswordInput(render_value=False))
 email_port=forms.IntegerField(min_value=1,max_value=65535,label='Porta SMTP')
 class Meta:
  model=SiteSettings
  fields=[field for fields in SECTIONS.values() for field in fields if field!='email_password']
  labels={'school_name':'Nome da escola','logo':'Logo da área de membros','support_email':'E-mail de suporte','whatsapp':'WhatsApp (somente números)','terms_url':'URL dos termos de uso','privacy_url':'URL da política de privacidade','mentor_display_name':'Nome exibido do mentor','mentor_label':'Etiqueta do mentor','team_display_name':'Nome exibido da equipe','access_period_text':'Texto explicativo do plano (não altera as datas)','signer_name':'Nome de quem assina','signer_role':'Cargo de quem assina','signature_image':'Imagem da assinatura','email_from_name':'Nome do remetente','email_from':'E-mail remetente','email_host':'Servidor SMTP','email_username':'Usuário SMTP','email_use_tls':'Usar TLS'}
 def __init__(self,*args,section='membros',**kwargs):
  super().__init__(*args,**kwargs)
  keys=SECTIONS.get(section,[]) if section is not None else set(self.data)|set(self.files)
  self.fields={key:field for key,field in self.fields.items() if key in keys}
