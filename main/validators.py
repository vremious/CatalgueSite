from django.core.exceptions import ValidationError


def validate_file_size(value):
    max_size = 5 * 1024 * 1024  # Максимальный размер 5 МБ
    if value.size > max_size:
        raise ValidationError(f'Файл "{value.name}" слишком большой. Максимально допустимый размер - 5 МБ.')


def validate_image_extension(value):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.JPG', 'JPEG', 'PNG', 'GIF']
    if not any(value.name.endswith(ext) for ext in valid_extensions):
        raise ValidationError('Неподходящее расширение файла. Допустимы: JPG, PNG, GIF.')


def validate_file_extension(value):
    valid_extensions = ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.DOC', '.DOCX', '.PDF', '.XLS', '.XLSX']
    if not any(value.name.endswith(ext) for ext in valid_extensions):
        raise ValidationError('Неподходящее расширение файла. Допустимы: DOC, DOCX, PDF, XLS, XLSX')
