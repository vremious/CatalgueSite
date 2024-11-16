document.addEventListener('DOMContentLoaded', function() {
    // Функция для валидации файлов
    const validateFileInput = (fileInput) => {
        const file = fileInput.files[0];
        const validDocumentExtensions = ['.doc', '.docx', '.xls', '.xlsx', '.pdf'];
        const validImageExtensions = ['.jpg', '.jpeg', '.png', '.gif'];
        const maxSize = 5 * 1024 * 1024;  // 5 MB

        // Проверяем, является ли input для изображений
        const isImageInput = fileInput.accept && fileInput.accept.includes('image/');

        if (file) {
            const fileName = file.name;
            const fileSize = file.size;

            // Валидация по расширению в зависимости от типа input
            const validExtensions = isImageInput ? validImageExtensions : validDocumentExtensions;
            const isValidExtension = validExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
            if (!isValidExtension) {
                alert(`Неподходящее расширение файла. Допустимы: ${validExtensions.join(', ')}`);
                fileInput.value = '';  // Очистить выбранный файл
                return false;
            }

            // Проверка на максимальный размер файла
            if (fileSize > maxSize) {
                alert(`Файл "${fileName}" слишком большой. Максимально допустимый размер - 5 МБ.`);
                fileInput.value = '';  // Очистить выбранный файл
                return false;
            }
        } else {
            // Если файл не выбран, ничего не делаем
            return true;
        }
        return true;
    };

    // Получаем все инлайн-фрагменты
    const forms = document.querySelectorAll('.inline-related');

    forms.forEach(form => {
        // Делегирование события на родительский элемент
        form.addEventListener('change', function(event) {
            if (event.target.matches('input[type="file"]')) {
                validateFileInput(event.target);
            }
        });

        // Слушаем добавление новых строк в динамически добавляемые формы
        const addRowLink = form.querySelector('.add-row a');
        if (addRowLink) {
            addRowLink.addEventListener('click', function() {
                // Здесь задержка не требуется, потому что событие "change" уже будет делегировано
            });
        }
    });
});