"""Fixture PDF ilustrativa criada somente pelo comando prepare_demo."""


def demo_pdf_bytes():
    stream = b'BT /F1 18 Tf 50 760 Td (Material de demonstracao) Tj 0 -35 Td /F1 12 Tf (O conteudo real sera fornecido pela equipe.) Tj ET'
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream',
    ]
    document = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = []
    for number, value in enumerate(objects, 1):
        offsets.append(len(document));document.extend(f'{number} 0 obj\n'.encode()+value+b'\nendobj\n')
    xref = len(document)
    document.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets:
        document.extend(f'{offset:010d} 00000 n \n'.encode())
    document.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return bytes(document)
