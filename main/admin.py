import datetime
from admin_totals.admin import ModelAdminTotals
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry

"""
Тут регистрируются разделы админки. Первично создаётся модель в разделе models, делается миграция,
далее регитсрируем тут. Также здесь можно настраивать, что будет уметь та или иная модель в админке.
"""


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'action_time', 'user', 'object_repr')
    list_filter = ('user__username',)
    search_fields = ['object_repr']
    date_hierarchy = 'action_time'


admin.site.register(LogEntry, LogEntryAdmin)


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
            self.message_user(request, "У вас нет привязанных филиалов.", level='error')
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
    list_max_show_all = 5000
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
        # form.base_fields['company'].initial = latest_object.company
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


class ExpiredDeviceSerialInline(admin.StackedInline):
    model = ExpiredDeviceSerial
    extra = 1


class AdminToFilialAdmin(admin.ModelAdmin):
    list_display = ['user', 'filial']


admin.site.register(TesterTime, TesterTimeAdmin)
admin.site.register(AdminToFilial, AdminToFilialAdmin)


class DeviceRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'service',  'device', 'contract_number', 'comment', 'answer', 'date']
    autocomplete_fields = ['device']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Фильтрация доступных сервисов для текущего пользователя
        if request.user.is_authenticated:
            # Получаем все сервисы, связанные с пользователем через Employee
            employee_services = Employee.objects.filter(user=request.user).values_list('service', flat=True)
            form.base_fields['service'].queryset = Service.objects.filter(id__in=employee_services)
        return form

    def save_model(self, request, obj, form, change, *args):
        if not change:
            obj.user = request.user
            obj.date = datetime.datetime.now()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='Service Admins'):
            return ['answer']
        elif request.user.is_superuser is True:
            return []
        else:
            return ['device', 'contract_number', 'comment']

    def get_queryset(self, request):
        if request.user.groups.filter(name='Service Admins'):
            return self.model.objects.filter(user=request.user.id)
        else:
            return self.model.objects.all()


admin.site.register(DeviceRequest, DeviceRequestAdmin)


class ExpiredDevicesAdmin(admin.ModelAdmin):
    list_display = ['company', 'model', 'filial', 'date_created', 'date_sell_until']
    autocomplete_fields = ['model']
    inlines = [ExpiredDeviceSerialInline]

    def company(self, obj):
        return obj.model.company

    def model(self, obj):
        return obj.model.model


admin.site.register(ExpiredDevice, ExpiredDevicesAdmin)


@admin.register(ExpiredDeviceSerial)
class ExpiredDeviceSerialAdmin(admin.ModelAdmin):
    list_display = ['entry', 'serial_number', 'date_sell_until']
    search_fields = ['entry__model__company__company', 'entry__model__model', 'serial_number']

    def date_sell_until(self, obj):
        # Предполагается, что obj.entry ссылается на экземпляр модели ExpiredDevices
        return obj.entry.date_sell_until if obj.entry else None




def logged_in_message(sender, user, request, **kwargs):
    """
    Add a welcome message when the user logs in
    """
    messages.info(request, "Добро пожаловать!")

    # messages.info(request, 'При необходимости обновления времени ВСЕГО оборудования на участке спуститесь вниз страницы "Наличие оборудования"')
    # messages.info(request, 'Нажмите на "Показать все" рядом с перечнем страниц')
    # messages.info(request, 'Выберите всё оборудование нажатием на самый верхний чекбокс вверху таблицы (Возле шапки "Сервисный центр")')
    # messages.info(request, 'Над шапкой таблицы возле "Сервисный центр" в поле "Действие" выбрать "Обновить дату и время внесения", после чего нажать на кнопку "Выполнить"')
    # messages.info(request, 'Это действие автоматически проставит текущее время на всех выбраных элементах.')


user_logged_in.connect(logged_in_message)
