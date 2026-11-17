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
