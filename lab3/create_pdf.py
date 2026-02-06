#!/usr/bin/env python3

import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def create_pdf():
    doc = SimpleDocTemplate('ProgLangRep3.pdf', pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        spaceAfter=15,
        spaceBefore=20
    )
    
    subheading_style = ParagraphStyle(
        'Subheading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        spaceAfter=10,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        fontName='Courier',
        leftIndent=20,
        spaceAfter=6,
        spaceBefore=6,
        borderColor='black',
        borderWidth=1,
        borderPadding=5
    )
    
    # Title page content
    story.append(Paragraph('Национальный исследовательский университет ИТМО', subtitle_style))
    story.append(Paragraph('Мегафакультет компьютерных технологий и управления', subtitle_style))
    story.append(Paragraph('Факультет программной инженерии и компьютерной техники', subtitle_style))
    
    story.append(Spacer(1, 40))
    
    story.append(Paragraph('Отчет по лабораторной работе №3', title_style))
    story.append(Paragraph('по курсу «Языки программирования»', title_style))
    
    story.append(Spacer(1, 60))
    
    story.append(Paragraph('<b>Выполнил:</b>', normal_style))
    story.append(Paragraph('Студент группы P4119', normal_style))
    story.append(Paragraph('М.С. Маршалов', normal_style))
    
    story.append(Spacer(1, 20))
    
    story.append(Paragraph('<b>Преподаватель:</b>', normal_style))
    story.append(Paragraph('Ю. Д. Кореньков', normal_style))
    
    story.append(Spacer(1, 60))
    
    story.append(Paragraph('Санкт-Петербург', subtitle_style))
    story.append(Paragraph('2026', subtitle_style))
    
    story.append(PageBreak())
    
    # Main content
    content = [
        ("Цель", "Разработать компилятор с языка программирования Simple в ассемблер для различных архитектур (x86-64 Linux, x86-64 Windows, RISC-V). Реализовать генерацию кода на основе графа потока управления, поддерживающий основные конструкции языка программирования."),
        
        ("Задачи", None),
        
        ("1. Реализовать парсер языка Simple", None),
        ("1.1. Разработать синтаксический анализатор для языка Simple", "Был реализован лексический и синтаксический анализатор для языка Simple с поддержкой основных конструкций."),
        ("1.2. Построить абстрактное синтаксическое дерево (AST)", "Парсер строит AST, которое затем преобразуется в граф потока управления."),
        ("1.3. Реализовать семантический анализ и проверку типов", "Реализована простая система типов, поддерживающая int, float, string и массивы."),
        
        ("2. Создать систему генерации кода", None),
        ("2.1. Реализовать построение графа потока управления (CFG)", "На основе AST строится CFG, состоящий из базовых блоков с операциями и переходами."),
        ("2.2. Разработать генераторы ассемблерного кода для x86-64 Linux", "Использует синтаксис NASM и системные вызовы Linux."),
        ("2.3. Реализовать генерацию кода для x86-64 Windows", "Использует синтаксис MASM и Windows API."),
        ("2.4. Создать генератор для архитектуры RISC-V", "Генерирует код в формате GCC для RISC-V."),
        
        ("3. Поддержать основные конструкции языка", None),
        ("3.1. Арифметические и логические операции", "Поддерживаются операции +, -, *, /, %, &&, ||, !, операции сравнения."),
        ("3.2. Условные операторы (if-else if-else)", "Реализована полная поддержка условных конструкций."),
        ("3.3. Циклы (while, do-while, for)", "Поддерживаются все три вида циклов."),
        ("3.4. Функции и вызовы встроенных функций", "Поддерживаются функции, printf, scanf, malloc, free."),
        
        ("4. Обеспечить кросс-платформенность", None),
        ("4.1. Реализовать абстракцию над целевыми платформами", "Создан единый интерфейс для всех генераторов."),
        ("4.2. Обеспечить совместимость с системными вызовами", "Адаптация под системные вызовы каждой платформы."),
        ("4.3. Поддержать различные конвенции вызовов", "Реализованы System V ABI для Linux и Microsoft x64 для Windows."),
        
        ("Ход работы", None),
        
        ("1. Разработка парсера языка Simple", "Был реализован лексический и синтаксический анализатор для языка Simple. Язык поддерживает объявления переменных, функции, управляющие конструкции и выражения."),
        
        ("Пример программы на языке Simple", """
function fibonacci() -> int {
    variable a -> int;
    variable b -> int;
    variable temp -> int;
    variable n -> int;
    
    a = 0;
    b = 1;
    n = 10;
    
    while (n > 0) {
        printf("%d\n", a);
        temp = a + b;
        a = b;
        b = temp;
        n = n - 1;
    }
    
    return a;
}
        """),
        
        ("2. Генерация графа потока управления", "На основе AST строится CFG, состоящий из базовых блоков. Каждый базовый блок содержит последовательность операций и переходы к другим блокам."),
        
        ("Структура базового блока", """
@dataclass
class BasicBlock:
    id: int
    operations: List[Operation]
    true_branch: Optional['BasicBlock']
    false_branch: Optional['BasicBlock'] 
    next_block: Optional['BasicBlock']
    is_loop_start: bool = False
    is_loop_end: bool = False
        """),
        
        ("3. Генераторы ассемблерного кода", "Реализованы три генератора кода для различных архитектур."),
        
        ("3.1. Генератор для x86-64 Linux", "Использует синтаксис NASM и системные вызовы Linux. Основные особенности: использует регистры RAX, RBX, RCX, RDX для вычислений, системные вызовы через syscall, стандартная конвенция вызовов System V ABI."),
        
        ("Пример генерации кода для Linux", """
section .text
global main

main:
    push rbp
    mov rbp, rsp
    
    ; Выделение места для локальных переменных
    sub rsp, 32
    
    ; a = 0
    mov qword [rbp-8], 0
    
    ; Цикл while
while_start:
    ; Условие n > 0
    mov rax, [rbp-24]
    test rax, rax
    jle while_end
    
    ; Тело цикла
    call printf
    jmp while_start
while_end:
    
    mov rsp, rbp
    pop rbp
    ret
        """),
        
        ("3.2. Генератор для x86-64 Windows", "Использует синтаксис MASM и Windows API. Ключевые отличия: использование регистров RAX, RCX, RDX, R8, R9 для аргументов, вызовы Windows API, другая конвенция вызовов Microsoft x64."),
        
        ("3.3. Генератор для RISC-V", "Генерирует код в формате GCC для архитектуры RISC-V: использует регистры x0-x31, системные вызовы через ecall, простая конвенция вызовов RISC-V."),
        
        ("Пример генерации кода для RISC-V", """
.text
.global main

main:
    ; Сохранение фрейма
    addi sp, sp, -32
    sw ra, 28(sp)
    
    ; a = 0
    li t0, 0
    sw t0, -8(fp)
    
    ; Цикл while
while_start:
    ; Условие n > 0
    lw t0, -24(fp)
    blez t0, while_end
    
    ; printf
    li a7, 93
    ecall
    
    j while_start
while_end:
    
    ret
        """),
        
        ("4. Тестирование и результаты", "Компилятор был протестирован на нескольких примерах: калькулятор, числа Фибоначчи, сортировка массива. Все примеры успешно компилируются и выполняются на всех трех поддерживаемых платформах."),
        
        ("5. Сборка и использование", "Для сборки проекта используется Makefile. Основные команды: make all - сборка всех примеров, make calculator-linux - сборка калькулятора для Linux, make calculator-riscv - сборка для RISC-V."),
        
        ("Выводы", "В ходе лабораторной работы был успешно разработан компилятор с языка Simple в ассемблер для трех архитектур. Основные достижения: реализован полный цикл компиляции, поддерживаются основные конструкции языка, обеспечена кросс-платформенность, продемонстрирована эффективность использования графа потока управления."),
    ]
    
    for title, text in content:
        if text is None:
            story.append(Paragraph(title, heading_style))
        elif title.startswith(('1.', '2.', '3.', '4.')) and not title.endswith(('Арифметические', 'Условные операторы', 'Циклы', 'Функции', 'Реализовать абстракцию', 'Обеспечить совместимость', 'Поддержать различные')):
            story.append(Paragraph(title, subheading_style))
            if text:
                story.append(Paragraph(text, normal_style))
        elif title.startswith(('1.1', '1.2', '1.3', '2.1', '2.2', '2.3', '2.4', '3.1', '3.2', '3.3', '3.4', '4.1', '4.2', '4.3')):
            story.append(Paragraph(title, subheading_style))
            if text:
                story.append(Paragraph(text, normal_style))
        elif title in ["Цель", "Задачи", "Ход работы", "Выводы"]:
            story.append(Paragraph(title, heading_style))
        elif "Пример" in title or "Структура" in title:
            story.append(Paragraph(title, subheading_style))
            story.append(Paragraph(text, code_style))
        else:
            story.append(Paragraph(title, subheading_style))
            if text and text.strip():
                if text.strip().startswith('function') or text.strip().startswith('@dataclass') or text.strip().startswith('section'):
                    story.append(Paragraph(text, code_style))
                else:
                    story.append(Paragraph(text, normal_style))
        
        story.append(Spacer(1, 12))
    
    # Signature lines
    story.append(Spacer(1, 40))
    story.append(Paragraph('______________ / М.С. Маршалов', normal_style))
    story.append(Paragraph('______________ / Ю.Д. Кореньков', normal_style))
    
    doc.build(story)
    print('PDF создан успешно: ProgLangRep3.pdf')

if __name__ == '__main__':
    create_pdf()