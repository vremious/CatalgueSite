import datetime

import dateutil.relativedelta
from django.core.validators import FileExtensionValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from transliterate import translit
from django.contrib.auth.models import User
from PIL import Image as PILImage

from main.validators import validate_file_size, validate_image_extension, validate_file_extension

"""
Тут прописываются модели ORM. Объявляя модель создаётся новая таблица в БД.
В случаее создания или изменения в этом разделе обязательно прописывать в терминале комманды:
python manage.py makemigrations
python manage.py migrate
Воизбежании проблем и конфликтов очень советую почитать официальную документацию, а все миграции отрабатывать
на тестовой БД, предвариельно выбрав её в settings.py
"""


class Purpose(models.Model):
    purpose = models.CharField(max_length=250, verbose_name='Назначение оборудования', choices=(
        ('На продажу', 'На продажу'),
        ('Абонентское', 'Абонентское')
    ))

    class Meta:
        verbose_name = 'Назначение оборудования'
        verbose_name_plural = 'Назначение оборудования'

    def __str__(self):
        return self.purpose


class Company(models.Model):
    company = models.CharField(max_length=50, verbose_name='Производитель', unique=True)

    class Meta:
        verbose_name = 'Производитель оборудования'
        verbose_name_plural = 'Производитель оборудования'
        ordering = ['company']

    def __str__(self):
        return self.company


class Type(models.Model):
    purpose = models.ForeignKey(Purpose, on_delete=models.CASCADE, default=1)
    type = models.CharField(max_length=50, verbose_name='Тип оборудования', unique=True)
    slug = models.SlugField(max_length=255, verbose_name='Ссылка', null=True, blank=True, editable=False)

    def my_slugify(self):
        return slugify(translit(self.type, 'ru', reversed=True))

    def save(self, *args, **kwargs):
        if self.slug is None or self.slug == 'slug':
            self.slug = self.my_slugify()
        super(Type, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Тип оборудования'
        verbose_name_plural = 'Тип оборудования'
        ordering = ['type']

    def __str__(self):
        return str(self.type)


class Filial(models.Model):
    filial = models.CharField(max_length=50, verbose_name="Филиал", unique=True)
    slug = models.SlugField(max_length=255, verbose_name='Ссылка', null=True, blank=True, editable=False)

    def my_slugify(self):
        return slugify(translit(self.filial, 'ru', reversed=True))

    def save(self, *args, **kwargs):
        if self.slug is None or self.slug == 'slug':
            self.slug = self.my_slugify()
        super(Filial, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ['filial']

    def __str__(self):
        return str(self.filial)


class Service(models.Model):
    service_centre = models.CharField(max_length=250, verbose_name='Сервисные центры')
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Филиал')

    class Meta:
        verbose_name = 'Сервисный центр'
        verbose_name_plural = 'Сервисные центры'
        unique_together = ['service_centre', 'filial']

    def __str__(self):
        return f'{self.service_centre}'


class AddFilterName1(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название параметра фильтра',
                            blank=True, null=True, unique=True)

    class Meta:
        verbose_name = 'Название фильтра'
        verbose_name_plural = 'Названия фильтра'

    def __str__(self):
        return self.name


class AddFilter1(models.Model):
    value = models.CharField(max_length=50, verbose_name='Параметр фильтра',
                             blank=True, null=True, unique=True)

    class Meta:
        verbose_name = 'Значение фильтра'
        verbose_name_plural = 'Значения фильтра'

    def __str__(self):
        return self.value


class Models(models.Model):
    type_fk = models.ForeignKey(Type, on_delete=models.CASCADE, verbose_name='Тип оборудования')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Производитель')
    model = models.CharField(max_length=50, verbose_name='Модель оборудования')
    actual = models.CharField(max_length=3, verbose_name='Актуально', choices=(
        ('Нет', 'Нет'),
        ('Да', 'Да')
    ), default='Нет')
    add_filter_name = models.ForeignKey(AddFilterName1, on_delete=models.CASCADE,
                                        verbose_name='Название дополнительного фильтра', blank=True, null=True)
    add_filter = models.ForeignKey(AddFilter1, on_delete=models.CASCADE, verbose_name='Значение фильтра',
                                   blank=True, null=True)

    def photo_upload(self, filename):
        return f'main/media/{self.type_fk.slug}/{filename}'

    #
    image = models.ImageField(upload_to=photo_upload, blank=True, null=True, verbose_name='Фото оборудования')
    price = models.FloatField(verbose_name='Стоимость в рассрочку', blank=True, null=True)
    split_period = models.IntegerField(verbose_name='Период рассрочки', blank=True, null=True)
    full_price = models.FloatField(verbose_name='Стоимость при единовременной оплате', blank=True, null=True)
    warranty = models.PositiveSmallIntegerField(verbose_name='Гарантия', blank=True, null=True)

    def clean(self):
        if self.split_period and not self.price:
            raise ValidationError({'price': ['Укажите цену']})
        elif not self.split_period and self.price:
            raise ValidationError({'split_period': ['Укажите срок рассрочки']})

    def split_price(self):
        if self.price % self.split_period == 0:
            return round(self.price // self.split_period, 0)
        else:
            return round(self.price / self.split_period, 2)

    #
    # # Функция для создания подкаталогов медиа по типу устройств, для запуска раскоментить,
    # # в терминале вызвать модель Model,
    # # запусить цикл с параметром .save()
    # def save(self, *args, **kwargs):
    #     super(Models, self).save(*args, **kwargs)
    #     if self.image.name:
    #         image_name = str(os.path.split(self.image.name)[-1])
    #         if self.image:
    #             initial_path = self.image.path
    #             if f'{self.type_fk.slug}' in self.image.path:
    #                 pass
    #             else:
    #                 if not os.path.exists(f'main/media/{self.type_fk.slug}'):
    #                     os.makedirs(f'main/media/{self.type_fk.slug}')
    #                 new_path = os.path.join('C:\\Users\\Denis\\PycharmProjects\\Catalgue_v2\\main\\media\\',
    #                                         self.type_fk.slug, image_name)
    #                 new_name = f'main/media/{self.type_fk.slug}/{image_name}'
    #                 shutil.copyfile(initial_path, new_path)
    #                 # os.rename(initial_path, new_path)
    #                 self.image.name = new_name
    #                 super(Models, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'
        unique_together = ('company', 'model')

    def __str__(self):
        return f'{self.company} {self.model}'


class Available(models.Model):
    model = models.ForeignKey(Models, on_delete=models.CASCADE, verbose_name='Модель оборудования')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Сервисный центр')
    available = models.CharField(max_length=20, verbose_name="Наличие", choices=(
        ('+', '+'),
        ('-', '-')
    ), default='-')
    quantity = models.PositiveSmallIntegerField(verbose_name='Количество', default='0')
    date = models.DateTimeField("Дата обновления", auto_now=True)

    def clean(self):
        cleaned_data = super().clean()
        if self.available == '-' and self.quantity != 0:
            raise ValidationError({'available': ['Исправьте значение на "+"']})
        elif self.available == '+' and self.quantity == 0:
            raise ValidationError({'available': ['Исправьте значение на "-"']})

    class Meta:
        ordering = ['model']
        verbose_name = 'Наличие оборудования'
        verbose_name_plural = 'Наличие оборудования'
        unique_together = ('service', 'model')

    def __str__(self):
        return str(f'{self.service}-{self.model}-{self.available}-{self.quantity}')


# Декоратор, который автоматизирует создание "наличие оборудования" на всех СЦ, при создании нового оборудования:
@receiver(post_save, sender=Models)
def create_new_available_objects(instance, created, **kwargs):
    for service_id in Service.objects.select_related().values_list('id', flat=True):
        if not Available.objects.select_related().filter(model=instance, service_id=service_id):
            choices = [Available(model=instance, service_id=service_id, available='-', quantity=0)]
            Available.objects.bulk_create(choices)
        else:
            pass


class TesterTime(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Сервисный центр')
    worktime = models.TextField(max_length=150, verbose_name='Время работы тестировщика')
    onduty = models.BooleanField(verbose_name='Тестировщик на месте')
    date = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = 'Время работы тестировщика'
        verbose_name_plural = 'Время работы тестировщика'

    def __str__(self):
        return str(f'{self.service}---------{self.worktime}----------{self.onduty}')


# Декоратор автоматически добавлюящий "Время работы тестировщика" при добавлении нового СЦ:
@receiver(post_save, sender=Service)
def create_new_available_testertime(instance, created, **kwargs):
    for service_id in Service.objects.values_list('id', flat=True):
        if not TesterTime.objects.filter(service=instance):
            TesterTime.objects.create(service=instance, onduty=False)
        else:
            pass


class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Сервисный центр',
                                null=True, blank=True)

    class Meta:
        verbose_name = "Привязка админов к СЦ"
        verbose_name_plural = 'Привязки админов к СЦ'
        unique_together = ['user', 'service']

    def __str__(self):
        return str(f'{self.user} - {self.service}')


class AdminToFilial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Филиал')

    class Meta:
        verbose_name = 'Привязка маркетинга'
        verbose_name_plural = 'Привязка маркетинга'


class DeviceRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, verbose_name="Пользователь")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, editable=True, null=True, blank=True,
                                verbose_name='Сервисный центр')
    device = models.ForeignKey(Models, on_delete=models.CASCADE, verbose_name='Устройство')
    contract_number = models.CharField(max_length=20, blank=True, verbose_name='Номер договора')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    answer = models.TextField(blank=True, null=True, verbose_name='Ответ на запрос')
    decision = models.CharField(verbose_name='Результат запроса', choices=(
        ('Принято', 'Принято'),
        ('Отклонено', 'Отклонено')), blank=True, null=True)
    date = models.DateTimeField(auto_created=True, editable=False, null=True, blank=True,
                                verbose_name='Дата создания заявки')

    class Meta:
        verbose_name = 'Запрос устройства'
        verbose_name_plural = 'Запрос устройтсв'


# #
# #
class ExpiredDevice(models.Model):
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, blank=False, null=False,
                               verbose_name='Филиал')
    model = models.ForeignKey(Models, on_delete=models.CASCADE, verbose_name='Модель устройства', blank=False,
                              null=False)
    date_created = models.DateTimeField(editable=False, auto_created=True, blank=False, verbose_name='Дата создания')
    date_sell_until = models.DateField(editable=True, null=True, blank=True, verbose_name="Реализовать до",
                                       default=datetime.date.today() + dateutil.relativedelta.relativedelta(months=2))

    class Meta:
        verbose_name = 'Срочно продать'
        verbose_name_plural = 'Срочно продать'
        unique_together = ['filial', 'model']

    def save(self, *args, **kwargs):
        self.date_created = datetime.datetime.now()
        if self.date_sell_until is None:
            self.date_sell_until = self.date_created + dateutil.relativedelta.relativedelta(months=2)
        super(ExpiredDevice, self).save(*args, **kwargs)

    def __str__(self):
        return str(f'{self.model}')


class ExpiredDeviceSerial(models.Model):
    entry = models.ForeignKey(ExpiredDevice, on_delete=models.CASCADE, null=False, verbose_name='Устройство')
    serial_number = models.CharField(max_length=50, blank=False, verbose_name='Серийный номер')
    sold = models.BooleanField(verbose_name='Продан', default=False)
    by_who = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Где продан')

    class Meta:
        verbose_name = 'Срочно продать (SN))'
        verbose_name_plural = 'Срочно продать (SN))'
        unique_together = ['entry', 'serial_number']

    def clean(self):
        super().clean()
        # Проверка валидации только если sold установлено в True
        if self.sold and not self.by_who:
            raise ValidationError('Если устройство продано, укажите где продано.')


class Refund(models.Model):
    date_created = models.DateTimeField(editable=False, auto_created=True, blank=False,
                                        verbose_name='Дата создания заявки')
    filial = models.ForeignKey(Filial, on_delete=models.DO_NOTHING, blank=True, null=True, verbose_name='Филиал')
    date_send_to_BT = models.DateField(blank=True, null=True, verbose_name='Дата отправки заявки в БТК')
    device = models.ForeignKey(Models, on_delete=models.DO_NOTHING, null=True, verbose_name='Устройство')
    serial_number = models.CharField(max_length=50, null=False, verbose_name='Серийный номер устройства')
    problem_description = models.TextField(verbose_name='Описание проблемы', blank=True)
    pre_barter = models.CharField(choices=(('Да', 'Да'), ('Нет', 'Нет')), max_length=3, blank=True,
                                  verbose_name="Предторг")
    description = models.TextField(verbose_name='Примечание', blank=True)
    date_approved_return = models.DateField(blank=True, null=True, verbose_name='Согласован возврат')

    def save(self, *args, **kwargs):
        self.date_created = datetime.datetime.now()
        super(Refund, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Возврат товара'
        verbose_name_plural = 'Возвраты товаров'
        unique_together = ['device', 'serial_number']

    def __str__(self):
        return str(f'{self.device}')


class RefundImage(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, verbose_name='Заявка на возврат', blank=False)

    def file_upload(self, filename):
        return f'main/media/refund_contracts/{self.refund.serial_number}/{filename}'

    image = models.ImageField(upload_to=file_upload, validators=[validate_file_size, validate_image_extension],
                              verbose_name='Фотографии')

    class Meta:
        verbose_name = 'Фото дефекта'
        verbose_name_plural = 'Фото дефектов'


class RefundDocs(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, verbose_name='Заявка на возврат', blank=False)

    def file_upload(self, filename):
        return f'main/media/refund_contracts/{self.refund.serial_number}/{filename}'

    docs = models.FileField(upload_to=file_upload, validators=[validate_file_size, validate_file_extension],
                             verbose_name='Документы')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

# Модуль сжимающий фото до 1920 пикселей по горизонтали с сохранением пропорций
@receiver(post_save, sender=RefundImage)
def compress_image(sender, instance, **kwargs):
    if instance.image:
        img_path = instance.image.path
        img = PILImage.open(img_path)

        # Устанавливаем максимальную ширину
        max_width = 1920

        # Получаем ширину и высоту изображения
        width, height = img.size

        # Проверяем, нужно ли изменять размер изображения
        if width > max_width:
            # Вычисляем коэффициент уменьшения
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)

            # Изменяем размер изображения
            img = img.resize((new_width, new_height))

            # Сохраняем изображение
            img.save(img_path, format='JPEG', quality=85)


# Декоратор добавляющий и убирающий оборудование взависимотси от актуальности:
@receiver(post_save, sender=Available)
def change_actual(**kwargs):
    for m in Models.objects.filter(type_fk__purpose=1).values_list('id', flat=True):
        if Available.objects.filter(model=m, available='+'):
            Models.objects.filter(id=m).update(actual='Да')
        elif Available.objects.filter(model=m, available='-'):
            Models.objects.filter(id=m).update(actual='Нет')


# Создание всего списка оборудования для новых СЦ
@receiver(post_save, sender=Service)
def create_devices_for_new_service_centers(instance, **kwargs):
    for model_id in Models.objects.select_related().values_list('id', flat=True):
        if not Available.objects.select_related().filter(model_id=model_id, service=instance):
            choices = [Available(model_id=model_id, service=instance, available='-', quantity=0)]
            Available.objects.bulk_create(choices)
