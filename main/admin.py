import datetime
from admin_totals.admin import ModelAdminTotals
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.utils.safestring import mark_safe

import main.models
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry

"""
Тут регистрируются разделы админки. Первично создаётся модель в разделе models, делается миграция,
далее регитсрируем тут. Также здесь можно настраивать, что будет уметь та или иная модель в админке.
"""


class CustomLogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'action_flag', '__str__')
    list_filter = ['content_type']

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs  # Суперпользователь видит все записи

        # # Получаем все сервисы, к которым относится пользователь
        # try:
        #     employee_services = Employee.objects.filter(user=request.user).values_list('service', flat=True)
        #     print(employee_services)
        # except Employee.DoesNotExist:
        #     return qs.none()  # Если у пользователя нет записи в Employee, ничего не показываем
        #
        # # Получаем пользователей, относящихся к этим сервисам
        # related_users = User.objects.filter(employee__service__in=employee_services)
        # print(related_users)
        #
        # # Получаем все заявки Refund, созданные пользователями из этих сервисов
        # related_refunds = Refund.objects.filter(user__in=related_users)
        # print(related_refunds)
        #
        # # Получаем IDs связанных Refund
        # related_refund_ids = related_refunds.values_list('id', flat=True)
        # print(related_refund_ids)
        # related_refund_ids_str = list(map(str, related_refund_ids))  # Приводим к строкам
        # refund_content_type = ContentType.objects.get_for_model(Refund)
        # # Фильтруем логи по объектам Refund, созданным пользователями из этих сервисов и действиям над ними
        # return qs.filter(object_id__in=related_refund_ids_str,
        #                  content_type=refund_content_type)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.register(LogEntry, CustomLogEntryAdmin)


class FilialAdmin(admin.ModelAdmin):
    list_display = ('filial', 'slug')


admin.site.register(Filial, FilialAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_centre', 'filial')
    list_filter = ['filial']
    list_editable = ['filial']
    search_fields = ['filial__filial', 'service_centre']


admin.site.register(Service, ServiceAdmin)


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')  # Added last_login


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
User = get_user_model()
admin.site.site_header = "Администрирование оборудования Белтелеком"
admin.site.site_title = "Панель администрирования"
admin.site.index_title = "Добро пожаловать!"
admin.site.register(AddFilter1)
admin.site.register(AddFilterName1)
admin.site.register(Purpose)
admin.site.register(Employee)


class CompanyAdmin(admin.ModelAdmin):
    search_fields = ['company']


admin.site.register(Company, CompanyAdmin)


class TypeAdmin(admin.ModelAdmin):
    list_display = ['type', 'slug']
    search_fields = ['type']


admin.site.register(Type, TypeAdmin)


class ModelsAdmin(admin.ModelAdmin):
    list_display = ['company', 'model', 'type_fk', 'price', 'split_period', 'warranty', 'actual']
    list_filter = ['type_fk__type', 'company']
    search_fields = ['model', 'company__company']
    list_per_page = 20
    list_max_show_all = 100000
    list_editable = ['actual', 'price', 'split_period', 'warranty']
    autocomplete_fields = ['company', 'type_fk']
    actions = ['mark_as_expired']

    def mark_as_expired(self, request, queryset):
        """
        Позволяет выбрать несколько устройств и отмечать их для срочной продажи.
        """
        # Получаем текущего пользователя
        current_user = request.user

        # Получаем все филиалы, к которым прикреплен пользователь
        user_filials = AdminToFilial.objects.filter(user=current_user).values_list('filial', flat=True)

        # Проверяем, что есть филиалы
        if not user_filials:
            self.message_user(request, "У вас нет полномочий - обратитесь к администратору сайта.", level='error')
            return

        # Для хранения новых записей
        expired_devices = []

        # Проверяем существующие записи в ExpiredDevice, чтобы не добавлять их снова
        existing_records = ExpiredDevice.objects.filter(model__in=queryset, filial_id__in=user_filials).values_list(
            'model_id', 'filial_id')

        for model in queryset:
            for filial_id in user_filials:
                # Проверяем, существует ли запись
                if (model.id, filial_id) not in existing_records:
                    expired_devices.append(ExpiredDevice(filial_id=filial_id, model=model,
                                                         date_created=datetime.datetime.now(),
                                                         date_sell_until=datetime.date.today() +
                                                                         dateutil.relativedelta.relativedelta(
                                                                             months=2)))

        # bulk_create для добавления всех записей за один запрос, если есть новые
        if expired_devices:
            ExpiredDevice.objects.bulk_create(expired_devices)
            self.message_user(request, "Выбранные устройства успешно добавлены для срочной продажи.")
        else:
            self.message_user(request, "Все выбранные устройства уже отмечены для срочной продажи.", level='warning')

    mark_as_expired.short_description = "Срочно продать"

    def get_form(self, request, obj=None, **kwargs):
        form = super(ModelsAdmin, self).get_form(request, obj, **kwargs)
        latest_object = Models.objects.latest('id')
        form.base_fields['model'].initial = latest_object.model
        form.base_fields['company'].initial = latest_object.company
        form.base_fields['type_fk'].initial = latest_object.type_fk
        form.base_fields['add_filter'].initial = latest_object.add_filter
        form.base_fields['add_filter_name'].initial = latest_object.add_filter_name
        form.base_fields['price'].initial = latest_object.price
        form.base_fields['split_period'].initial = latest_object.split_period
        return form

    class Media:
        js = ['js/admin_filter.js']


admin.site.register(Models, ModelsAdmin)


@admin.action(description="Обновить дату и время внесения")
def update(self, request, queryset):
    queryset.update(date=datetime.datetime.now())


@admin.register(Available)
class AvailableAdmin(ModelAdminTotals):
    list_per_page = 20
    list_max_show_all = 100000
    save_as = True

    @admin.display(ordering='model__type_fk__type', description='Тип')
    def type(self, obj):
        return obj.model.type_fk

    @admin.display(ordering='model__company__company', description='Производитель')
    def company(self, obj):
        return obj.model.company

    @admin.display(ordering='model__model', description='Модель')
    def model(self, obj):
        return obj.model.model

    class Media:
        js = ['js/admin_filter.js']

    def get_queryset(self, request):
        if Employee.objects.filter(user=request.user.id):
            var = Employee.objects.filter(user=request.user.id).values_list('service_id', flat=True)
            return self.model.objects.filter(service__in=var)
        else:
            return self.model.objects.all()

    def get_form(self, request, obj=None, **kwargs):
        form = super(AvailableAdmin, self).get_form(request, obj, **kwargs)
        latest_object = Available.objects.latest('date')
        form.base_fields['model'].initial = latest_object.model
        form.base_fields['quantity'].initial = latest_object.quantity
        form.base_fields['available'].initial = latest_object.available

        return form

    list_filter = ['model__type_fk', 'model__company', 'available', 'service']
    list_editable = ['available', 'quantity']
    list_display = ['service', 'type', 'company', 'model', 'date', 'available', 'quantity']
    list_totals = [('quantity', Sum)]
    search_fields = ['model__company__company', 'model__model']
    actions = [update]


class TesterTimeAdmin(admin.ModelAdmin):
    save_as = True

    def get_queryset(self, request):
        if Employee.objects.filter(user=request.user.id):
            var = Employee.objects.filter(user=request.user.id).values_list('service_id', flat=True)
            return self.model.objects.filter(service__in=var)
        else:
            return self.model.objects.all()

    def get_form(self, request, obj=None, **kwargs):
        form = super(TesterTimeAdmin, self).get_form(request, obj, **kwargs)
        latest_object = TesterTime.objects.latest('date')
        form.base_fields['worktime'].initial = latest_object.worktime

        return form

    list_display = ['service', 'worktime', 'onduty']
    list_editable = ['worktime', 'onduty']


class AdminToFilialAdmin(admin.ModelAdmin):
    list_display = ['user', 'filial']


admin.site.register(TesterTime, TesterTimeAdmin)
admin.site.register(AdminToFilial, AdminToFilialAdmin)


class DeviceRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'device', 'contract_number', 'comment', 'answer', 'decision', 'date']
    autocomplete_fields = ['device']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Фильтрация доступных сервисов для текущего пользователя
        if request.user.is_authenticated and request.user.groups.filter(name='Service Admins').exists():
            if obj is None:
                # Получаем все сервисы, связанные с пользователем через Employee
                try:
                    employee_services = Employee.objects.filter(user=request.user).values_list('service', flat=True)
                    form.base_fields['service'].queryset = Service.objects.filter(id__in=employee_services)
                except:
                    pass
            else:
                if 'contract_number' in form.base_fields:
                    form.base_fields.pop('contract_number')
            return form
        elif request.user.is_superuser is True:
            form.base_fields['service'].queryset = Service.objects.select_related()
        return form

    def save_model(self, request, obj, form, change, *args):
        if not change:
            obj.user = request.user
            obj.date = datetime.datetime.now()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='Service Admins'):
            return ['answer', 'decision']
        elif request.user.is_superuser is True:
            return []
        else:
            return ['service', 'device', 'contract_number', 'comment']

    def get_queryset(self, request):
        marketing = AdminToFilial.objects.filter(user=request.user).values_list('filial', flat=True)
        # print(marketing)
        if request.user.groups.filter(name='Service Admins'):
            return self.model.objects.filter(user=request.user.id)
        elif request.user.is_superuser is True:
            return self.model.objects.all()
        elif request.user.groups.filter(name='marketing'):
            return self.model.objects.filter(service__filial__in=marketing)

    def get_list_display(self, request):
        if request.user.groups.filter(name='Service Admins'):
            return ['user', 'service', 'device', 'comment', 'answer', 'decision', 'date']
        elif request.user.groups.filter(name='marketing') or request.user.is_superuser is True:
            return ['user', 'service', 'device', 'contract_number', 'comment', 'answer', 'decision', 'date']

    # def get_exclude(self, request, obj=None):
    #     if request.user.groups.filter(name='Service Admins'):
    #         return ['contract_number']


admin.site.register(DeviceRequest, DeviceRequestAdmin)


class ExpiredDeviceSerialInline(admin.StackedInline):
    model = ExpiredDeviceSerial
    extra = 1


class ExpiredDevicesAdmin(admin.ModelAdmin):
    list_display = ['company', 'model', 'filial', 'date_created', 'date_sell_until']
    search_fields = ['model__model', 'model__company__company']
    autocomplete_fields = ['model']
    inlines = [ExpiredDeviceSerialInline]

    def company(self, obj):
        return obj.model.company

    def model(self, obj):
        return obj.model.model

    def get_queryset(self, request):
        if request.user.groups.filter(name='marketing'):
            marketing = AdminToFilial.objects.filter(user=request.user).values_list('filial', flat=True)
            return self.model.objects.filter(filial_id__in=marketing)
        elif request.user.is_superuser is True:
            return self.model.objects.all()


admin.site.register(ExpiredDevice, ExpiredDevicesAdmin)


@admin.register(ExpiredDeviceSerial)
class ExpiredDeviceSerialAdmin(admin.ModelAdmin):
    list_display = ['entry', 'filial', 'serial_number', 'date_sell_until', 'sold', 'by_who']
    search_fields = ['entry__model__company__company', 'entry__model__model', 'serial_number']

    def get_list_editable(self, request):
        if request.user.groups.filter(name='Service Admins'):
            self.list_editable.append('sold', 'by_who')

    @admin.display(description='Продать до')
    def date_sell_until(self, obj):
        # Предполагается, что obj.entry ссылается на экземпляр модели ExpiredDevices
        return obj.entry.date_sell_until if obj.entry else None

    @admin.display(description='Филиал')
    def filial(self, obj):
        return obj.entry.filial

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='Service Admins'):
            return ['entry', 'serial_number', 'date_sell_until']
        elif request.user.groups.filter(name='marketing'):
            return ['sold', 'by_who']
        else:
            return ['by_who']

    def get_queryset(self, request):
        marketing = AdminToFilial.objects.filter(user=request.user).values_list('filial', flat=True)
        service = Employee.objects.select_related().filter(user=request.user).values_list('service', flat=True)
        filial = Filial.objects.select_related().filter(service__in=service).values_list('id', flat=True)
        if request.user.groups.filter(name='Service Admins'):
            return self.model.objects.filter(entry__filial_id__in=filial)
        elif request.user.is_superuser is True:
            return self.model.objects.all()
        else:
            return self.model.objects.filter(entry__filial_id__in=marketing)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Фильтрация доступных сервисов для текущего пользователя
        if request.user.is_authenticated and request.user.groups.filter(name='Service Admins'):
            # Получаем все сервисы, связанные с пользователем через Employee
            employee_services = Employee.objects.filter(user=request.user).values_list('service', flat=True)
            form.base_fields['by_who'].queryset = Service.objects.filter(id__in=employee_services)
        elif request.user.is_superuser is True:
            pass
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "by_who":
            # Ограничиваем доступные сервисы только теми, которые связаны с текущим пользователем
            if request.user.is_authenticated:
                employee_services = Employee.objects.filter(user=request.user).values_list('service', flat=True)
                kwargs["queryset"] = Service.objects.filter(id__in=employee_services)
            elif request.user.is_superuser or request.user.groups.filter(name='marketing'):
                kwargs["queryset"] = Service.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RefundImageInline(admin.TabularInline):
    model = RefundImage
    extra = 1  # Количество пустых форм для добавления новых документов
    fields = ['image_tag', 'image']
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />')
        return ""


class RefundDocsInline(admin.TabularInline):
    model = RefundDocs
    extra = 1  # Количество пустых форм для добавления новых документов


class RefundAdmin(admin.ModelAdmin):
    inlines = [RefundImageInline, RefundDocsInline]  # Используем inline для добавления документов
    list_display = ('date_created', 'user', 'device', 'serial_number', 'problem_description', 'pre_barter',
                    'description', 'date_approved_return', 'by_who_changed', 'date_changed')
    autocomplete_fields = ['device']
    readonly_fields = ('date_created',)
    actions = ['delete_selected_devices']

    class Media:
        js = ('js/docs_validator.js',)

    def get_actions(self, request, *args, **kwargs):
        actions = super().get_actions(request)
        avalible_actions = {}
        if request.user.is_superuser:
            return actions
        else:
            return avalible_actions

    def delete_selected_devices(self, request, queryset):
        for refund in queryset:
            # Удаляем все связанные фотографии и их файлы перед удалением устройства
            for photo in refund.refundimage_set.all():
                if photo.image and os.path.isfile(photo.image.path):
                    os.remove(photo.image.path)
                photo.delete()
        for refund in queryset:
            # Удаляем все связанные документы и их файлы перед удалением устройства
            for docs in refund.refunddocs_set.all():
                if docs.docs and os.path.isfile(docs.docs.path):
                    os.remove(docs.docs.path)
                docs.delete()
                # Удаляем экземпляр документы после удаления файла
            refund.delete()  # Удаляем экземпляр устройства

        self.message_user(request, "Выбранные устройства и их изображения успешно удалены.")

    delete_selected_devices.short_description = "Удалить выбраные устройства и связанные изображения"

    def save_model(self, request, obj, form, change, *args):
        if not change:
            obj.user = request.user
            obj.date_created = datetime.datetime.now()
        else:
            obj.by_who_changed = request.user
            obj.date_changed = datetime.datetime.now()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='marketing'):
            return ['user', 'pre_barter', 'device', 'serial_number', 'problem_description', 'filial']
        elif request.user.is_superuser:
            return []
        else:
            return ['user', 'date_send_to_BT', 'description', 'date_approved_return']

    def get_queryset(self, request):
        qs = super(RefundAdmin, self).get_queryset(request)
        filial = AdminToFilial.objects.filter(user=request.user).values_list('filial', flat=True)

        if request.user.is_superuser is True:
            return qs
        elif request.user.groups.filter(name='marketing'):
            return qs.filter(filial__in=filial)
        # elif request.user.groups.filter(name='overseer'):
        #     return qs.filter(user__in=)
        else:
            return qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "filial":
            # Ограничиваем доступные сервисы только теми, которые связаны с текущим пользователем
            if request.user.is_authenticated and not request.user.is_superuser:
                services = Employee.objects.filter(user=request.user).values_list('service_id', flat=True)
                filials = Service.objects.filter(id__in=services).values_list('filial_id', flat=True)
                filial = AdminToFilial.objects.filter(user=request.user).values_list('filial_id', flat=True)
                kwargs["queryset"] = Filial.objects.filter(id__in=filial or filials)
            elif request.user.is_superuser:
                kwargs["queryset"] = Filial.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Refund, RefundAdmin)


def logged_in_message(sender, user, request, **kwargs):
    """
    Add a welcome message when the user logs in
    """
    messages.info(request, "Добро пожаловать!")

    messages.info(request, 'Нововведения на сайте:')
    messages.info(request, 'Появилась возможность запрашивать оборудование у маркетологов в разделе "Запрос устройств".'
                           ' Для запроса нужно выбрать интересующую модель оборудование, указать договор, на который'
                           ' будет выдаваться устройство, по желанию - оставить комментарий. Специалист маркетинга'
                           'может оставить ответ на вашу заявку и определить её статус (заявка принята или отклонена).')
    messages.info(request, 'Появился раздел "Срочно продать (SN)" - в нём содержатся серийные номера устройств, которые'
                           ' первостепенны к продаже. Назначает их отдел маркетинга.')
    messages.info(request, 'Специалистам СЦ большая просьба - для избежания путаницы, если у Вас была реализована'
                           ' единица товара с серийным '
                           'номером из списка - проставьте чекбокс "продан" и Ваш СЦ в "Срочно продать (SN)", после чего'
                           ' нажмите кнопку сохранить. Эти действия уберут серийный номер с карточки товара на сайте.'
                           ' Заранее спасибо!')
    # messages.info(request, 'Это действие автоматически проставит текущее время на всех выбраных элементах.')


user_logged_in.connect(logged_in_message)
