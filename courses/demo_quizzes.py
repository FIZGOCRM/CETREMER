"""Perguntas ilustrativas copiadas de QB.c1 e QB.p1 do protótipo V2.

Somente prepare_demo consome estes dados; não representam o conteúdo real.
"""

DEMO_LESSON_QUESTIONS = {
    'cardiologia': [
        ('Qual é o primeiro passo ao receber um paciente grave no pronto-socorro?',
         ['Pedir exames laboratoriais', 'Garantir a segurança e checar a responsividade', 'Colher a história completa', 'Prescrever analgesia'], 1,
         'Segurança e responsividade vêm antes de tudo. Depois vem a avaliação sistematizada.'),
        ('A classificação de risco na chegada serve principalmente para:',
         ['Definir o diagnóstico final', 'Priorizar quem precisa ser atendido primeiro', 'Substituir a avaliação médica', 'Reduzir o número de exames'], 1,
         'Ela organiza a fila pela gravidade, não pela ordem de chegada.'),
    ],
    'plantao': [
        ('Paciente que conversa em frases completas: o que isso indica sobre a via aérea?',
         ['Está obstruída', 'Está pérvia neste momento', 'Precisa de intubação', 'Nada'], 1,
         'Falar com frases completas indica via aérea pérvia e respiração razoável, no momento.'),
        ('Com vários pacientes no início do plantão, o que priorizar?',
         ['A ordem de chegada', 'A gravidade e o risco de piora', 'Quem reclama mais', 'Os pacientes que já estavam em observação'], 1,
         'Comece por quem pode piorar mais rápido.'),
    ],
}


# Avaliações do objeto C do mesmo protótipo; não há comentário nesse banco.
DEMO_FINAL_QUESTIONS = {
    'cardiologia': [
        ('Na avaliação inicial do paciente grave, qual sequência é recomendada?', ['ABCDE: via aérea, respiração, circulação, neurológico, exposição', 'Anamnese completa antes do exame físico', 'Exames laboratoriais antes da estabilização', 'Exame neurológico primeiro'], 0),
        ('Supradesnivelamento de ST em duas derivações contíguas sugere:', ['Pericardite crônica', 'IAM com supra de ST', 'Hipocalemia', 'Bloqueio de ramo direito isolado'], 1),
        ('Taquiarritmia com instabilidade hemodinâmica. Conduta imediata:', ['Observar e repetir ECG em 1 hora', 'Betabloqueador oral', 'Cardioversão elétrica sincronizada', 'Alta com retorno ambulatorial'], 2),
        ('Meta de tempo porta-balão na angioplastia primária:', ['Até 30 minutos', 'Até 90 minutos', 'Até 6 horas', 'Até 24 horas'], 1),
    ],
    'plantao': [
        ('Qual ferramenta estrutura a passagem de plantão?', ['SOAP', 'SBAR', 'APGAR', 'CHA2DS2-VASc'], 1),
        ('Na suspeita de sepse, o antimicrobiano deve ser iniciado:', ['Após resultado da hemocultura', 'Na primeira hora', 'Em até 24 horas', 'Só se houver febre'], 1),
        ('O que diferencia emergência de urgência hipertensiva?', ['O valor da pressão diastólica', 'A idade do paciente', 'Lesão aguda de órgão-alvo', 'O uso prévio de anti-hipertensivo'], 2),
        ('Paciente com rebaixamento de consciência. O primeiro exame à beira-leito é:', ['Tomografia de crânio', 'Glicemia capilar', 'Punção lombar', 'Eletroencefalograma'], 1),
    ],
}
