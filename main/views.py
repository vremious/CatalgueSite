from django.views.generic import ListView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, renderers, request
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from django.db.models import Q
from .serializer import ModelsSerializer, CompanySerializer, TypeSerializer
from .models import *

"""
Это раздел отображений (views), нужен он для передачи объектов из базы данных и дальнейшего использования их
на страницах html и в REST запросах.

"""


# viewsets нужны для отображения элементов бд в REST составляющей
class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()  # тут выбираем queryset из БД, в данном случае все объекты модели Type
    serializer_class = TypeSerializer  # тут ссылаемся на класс serializer из файла serializer.py
    # с которым будет взаимодействовать viewset
    filter_backends = [DjangoFilterBackend]  # подключаем модуль фильтрации
    # filterset_fields = ['id', 'company']


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by('id')  # выборка всех моделей Company, упорядоченная по id
    serializer_class = CompanySerializer  # ссылаемся на сериализатор для этого viewset
    filter_backends = [DjangoFilterBackend]  # подключаем модуль фильтрации
    filterset_fields = ['id', 'company']  # выбираем поля по которым фильтруем


class ModViewSet(viewsets.ModelViewSet):
    authentication_classes = [BasicAuthentication]  # подключаем аутентефикацию по логину и паролю (как в админке)
    permission_classes = [IsAuthenticated]  # настройка доступа для только авторизованных пользователей (иначе 400)
    queryset = Models.objects.all()  # тут выбираем queryset из БД
    serializer_class = ModelsSerializer  # тут ссылаемся на класс serializer из файла serializer.py
    renderer_classes = [JSONRenderer]  # определяем рендер страницы (в данном случае JSON)
    filter_backends = [DjangoFilterBackend]  # подключаем модуль фильтрации
    filterset_fields = ['id', 'model', 'company__company', 'type_fk__type']  # выбираем поля по которым фильтруем


"""
Ниже идут ListView объекты. Они нужны только для HTML страниц.
"""


# Это view для стартовой страницы (на которой предлагает выбрать филиал)
class Homing(ListView):
    model = Filial  # выбор модели из котрой будут браться объекты БД
    template_name = "main/homing.html"  # ссылка на шаблон HTML на котром будут отрисовываться объекты


# Главная страница сайта (с типами оборудования)
class MainPage(ListView):
    model = Models  # выбор модели из котрой будут браться объекты БД
    template_name = "main/category_detail.html"  # ссылка на шаблон HTML на котром будут отрисовываться объекты
    context_object_name = 'models'  # имя модели вызванной выше для использования в шаблоне HTML

    # функция ниже позволяет создать дополнительные объекты для использования их в HTML шаблоне
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["testertime"] = TesterTime.objects.all().select_related('service').filter(
            service__filial__slug=self.kwargs['slug']  # объект вкладки "График работы тестировщиков"
        ).order_by('service')
        context['typed'] = Available.objects.select_related('model__type_fk', 'model__type_fk__purpose',
                                                            'service__filial').filter(model__actual='Да').order_by(
            'model__type_fk_id', 'model__id')
        context['filial'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      quantity__gt=0, model__actual='Да').order_by(
            'model__type_fk_id', 'model__id')
        context['typed1'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      model__actual='Да').order_by(
            'model__type_fk', 'model__id')
        context['type'] = Type.objects.select_related('purpose')
        context['image'] = Models.objects.values_list('image', 'id').first()
        context['city'] = Filial.objects.select_related().filter(slug__exact=self.kwargs['slug'])[0]  # Название филиала
        context['main_button'] = ''
        context['city17'] = self.kwargs['slug']
        return context


# Страница с оборудованием из выбранной категории
class CategoryPage(ListView):
    model = Models
    template_name = "main/upu4.html"
    context_object_name = 'models'

    # Функция ниже нужна для получения выборки из БД взависимости от значений контекстных фильтров на странице
    # и последующего формирования отображения моделей. По сути заменяет параметр model выше.
    def get_queryset(self):
        qs1 = Available.objects.select_related('model', 'service', 'model__company',
                                               'model__add_filter_name', 'model__add_filter').filter(
            model__type_fk__slug=self.kwargs['cat_slug'], service__filial__slug=self.kwargs['slug'],
            model__actual='Да').order_by(
            self.request.GET.get('sort', default='model__company__company'), 'model__model',
            'service__service_centre')
        expired_qs = ExpiredDevice.objects.select_related().filter(
            filial__slug__exact=self.kwargs['slug'],
            model__type_fk__slug=self.kwargs['cat_slug'])
        try:
            expired = [i.model.id for i in expired_qs if expired_qs]
        except Exception:
            expired = []
        if self.request.GET.get('Company') or self.request.GET.get('Model') or self.request.GET.get('Service') \
                or self.request.GET.get('Available') or self.request.GET.get('Add_filter') or \
                self.request.GET.get('Expired'):
            if self.request.GET.get('Add_filter'):
                return qs1.filter(
                    model__company__company__icontains=self.request.GET.get('Company'),
                    model__model__icontains=self.request.GET.get('Model'),
                    service__service_centre__icontains=self.request.GET.get('Service'),
                    available__icontains=self.request.GET.get('Available'),
                    model__add_filter__value__icontains=self.request.GET.get('Add_filter'),
                )
            elif self.request.GET.get('Expired'):
                return qs1.filter(
                    model__company__company__icontains=self.request.GET.get('Company'),
                    model__model__icontains=self.request.GET.get('Model'),
                    service__service_centre__icontains=self.request.GET.get('Service'),
                    available__icontains=self.request.GET.get('Available'),
                    model_id__in=expired
                )
            elif self.request.GET.get('Expired') and self.request.GET.get('Add_filter'):
                return qs1.filter(
                    model__company__company__icontains=self.request.GET.get('Company'),
                    model__model__icontains=self.request.GET.get('Model'),
                    service__service_centre__icontains=self.request.GET.get('Service'),
                    available__icontains=self.request.GET.get('Available'),
                    model__add_filter__value__icontains=self.request.GET.get('Add_filter'),
                    model_id__in=expired

                )
            else:
                return qs1.filter(
                    model__company__company__icontains=self.request.GET.get('Company'),
                    model__model__icontains=self.request.GET.get('Model'),
                    service__service_centre__icontains=self.request.GET.get('Service'),
                    available__icontains=self.request.GET.get('Available'),

                )
        if Type.objects.select_related().filter(purpose__purpose='Абонентское', slug=self.kwargs['cat_slug']):
            return qs1
        else:
            return qs1.filter(available='+')

    # функция ниже позволяет создать дополнительные объекты для использования их в HTML шаблоне
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_add'] = Models.objects.select_related().filter(
            type_fk__slug=self.kwargs['cat_slug'], available__service__filial__slug=self.kwargs['slug'],
            actual='Да', available__available='+').values_list('add_filter_name__name', flat=True)
        context["testertime"] = TesterTime.objects.select_related('service').filter(
            service__filial__slug=self.kwargs['slug']
        ).order_by('service')
        context["available"] = Available.objects.select_related(
            'model', 'service').filter(service__filial__slug=self.kwargs['slug'], model__actual="Да").order_by(
            'service__id')
        context["available_f"] = Available.objects.select_related('model', 'service').filter(
            model__type_fk__slug=self.kwargs['cat_slug'],
            service__filial__slug=self.kwargs['slug']).order_by(
            'service__id')
        context['typed'] = Models.objects.select_related('type_fk').filter(actual='Да').order_by('type_fk_id')
        context['typed1'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      model__actual='Да').order_by(
            'model__type_fk')
        context['test'] = Models.objects.select_related('type_fk', 'add_filter_name', 'company').filter(
            type_fk__slug=self.kwargs['cat_slug'], available__service__filial__slug=self.kwargs['slug'],
            actual='Да', available__available='+').order_by(
            'company__company')
        context['title'] = Type.objects.select_related().filter(slug__exact=self.kwargs['cat_slug'])[0]
        context['service'] = Service.objects.all()
        context['quantity'] = self.request.GET.get('quantity', default=8)
        context['sort'] = self.request.GET.get('sort', default='model__company__company')
        context['filial'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      quantity__gt=0, model__actual='Да').order_by(
            'model__type_fk_id', 'model__id')
        context['city'] = Filial.objects.select_related().filter(slug__exact=self.kwargs['slug'])[0]
        context['main_button'] = '/' + Filial.objects.select_related().filter(
            filial__exact=context['city']).values_list('slug', flat=True)[0] + '/'
        context['city17'] = Filial.objects.select_related().filter(
            filial__exact=context['city']).values_list('slug', flat=True)[0]
        expired_qs = ExpiredDevice.objects.select_related().filter(
            filial__slug__exact=self.kwargs['slug'],
            model__type_fk__slug=self.kwargs['cat_slug'])
        context['expired_serials_qs'] = ExpiredDeviceSerial.objects.select_related().filter(
            entry__filial__slug__exact=self.kwargs['slug'],
            entry__model__type_fk__slug=self.kwargs['cat_slug'],
            entry__model_id__in=self.object_list.values_list('model_id', flat=True),
            sold=False,
            )
        try:
            context['expired'] = [i.model.id for i in expired_qs if expired_qs]
            context['expired_sn'] = [i.serial_number for i in  context['expired_serials_qs'] if i.entry.model.id in self.object_list.values_list('model', flat=True)]
        except:
            context['expired'] = []
            context['expired_sn'] = []

        return context


# View для результатов  поиска через строчку поиска в верхней части страницы
class SearchResults(ListView):
    model = Available
    template_name = 'main/searchresults.html'
    context_object_name = 'models'

    # Функция ниже нужна для получения выборки из БД взависимости от значений контекстных фильтров на странице
    # и последующего формирования отображения моделей. По сути заменяет параметр model выше.
    def get_queryset(self):
        sort = self.request.GET.get('sort', default='model__company__company')
        qs = Available.objects.select_related().filter(Q(model__actual="Да") &
                                                       Q(service__filial__slug=self.kwargs['slug']) &
                                                       Q(model__model__contains=self.request.GET.get('Search')) &
                                                       Q(available='+')).order_by(sort, 'model__model',
                                                                                  'service__service_centre')

        qs2 = Available.objects.select_related().filter(Q(model__actual="Да") &
                                                        Q(service__filial__slug=self.kwargs['slug']) &
                                                        Q(model__model__contains=self.request.GET.get('Search')) &
                                                        Q(model__type_fk__purpose__purpose='Абонентское')).order_by(
            sort, 'model__model', 'service__service_centre')

        qs3 = qs | qs2
        company = self.request.GET.get('Company')
        type_filter = self.request.GET.get('Type')
        expire = self.request.GET.get('Expired')
        try:
            expired = [i.model.id for i in
                       ExpiredDevice.objects.select_related().filter(filial__slug__exact=self.kwargs['slug'])]
        except:
            expired = []

        if company or type_filter or expire:
            qs = qs3.filter(Q(model__company__company__icontains=self.request.GET.get('Company')) &
                            Q(model__type_fk__type__icontains=type_filter)).order_by(sort, 'model__model',
                                                                                     'service__service_centre')
            if not expire:
                return qs
            else:
                return qs.filter(model_id__in=expired)
        return qs3

    # функция ниже позволяет создать дополнительные объекты для использования их в HTML шаблоне
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Результаты поиска'
        context["available"] = Available.objects.select_related(
            'model', 'service').filter(service__filial__slug=self.kwargs['slug'], model__actual="Да").order_by(
            'service__id')
        context['city'] = Filial.objects.select_related().filter(slug__exact=self.kwargs['slug'])[0]
        context['city17'] = Filial.objects.select_related().filter(
            filial__exact=context['city']).values_list('slug', flat=True)[0]
        context["available_f"] = Available.objects.select_related('model', 'service').filter(
            model__model__contains=self.request.GET.get('Search'),
            service__filial__slug=self.kwargs['slug']).order_by(
            'service__id')
        context["testertime"] = TesterTime.objects.select_related('service').filter(
            service__filial__slug=self.kwargs['slug']
        ).order_by('service')
        context['filial'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      quantity__gt=0, model__actual='Да').order_by(
            'model__type_fk_id', 'model__id')
        context['typed1'] = Available.objects.select_related().filter(service__filial__slug=self.kwargs['slug'],
                                                                      model__actual='Да').order_by(
            'model__type_fk')
        context['quantity'] = self.request.GET.get('quantity', default=8)
        context['sort'] = self.request.GET.get('sort', default='model__company__company')
        context['search'] = self.request.GET.get('Search')
        context['company'] = self.request.GET.get('Company')
        context['type_filter'] = self.request.GET.get('Type')
        context['customer_devices_filter'] = Models.objects.select_related().filter(
            model__contains=self.request.GET.get('Search'), available__service__filial__slug=self.kwargs['slug'],
            type_fk__purpose__purpose='Абонентское')
        if context['type_filter']:
            context['company_filter'] = Models.objects.select_related('type_fk', 'add_filter_name', 'company').filter(
                type_fk__type__icontains=context['type_filter'],
                model__contains=self.request.GET.get('Search'), available__service__filial__slug=self.kwargs['slug'],
                actual='Да', available__available='+').order_by(
                'company__company') | context['customer_devices_filter']
        else:
            context['company_filter'] = Models.objects.select_related('type_fk', 'add_filter_name', 'company').filter(
                model__contains=self.request.GET.get('Search'), available__service__filial__slug=self.kwargs['slug'],
                actual='Да', available__available='+').order_by(
                'company__company') | context['customer_devices_filter']

        context['type_filtered'] = Models.objects.select_related('type_fk', 'add_filter_name', 'company').filter(
            model__contains=self.request.GET.get('Search'), available__service__filial__slug=self.kwargs['slug'],
            actual='Да', available__available='+').order_by(
            'type_fk__type') | context['customer_devices_filter']
        expired_qs = ExpiredDevice.objects.select_related().filter(
            filial__slug__exact=self.kwargs['slug'],
            )
        context['expired_serials_qs'] = ExpiredDeviceSerial.objects.select_related().filter(
            entry__filial__slug__exact=self.kwargs['slug'],
            entry__model_id__in=self.object_list.values_list('model_id', flat=True),
            sold=False,
            )
        try:
            context['expired'] = [i.model.id for i in expired_qs if expired_qs]
            context['expired_sn'] = [i.serial_number for i in context['expired_serials_qs'] if i.entry.model.id in
                                     self.object_list.values_list('model', flat=True)]
        except:
            context['expired'] = []
            context['expired_sn'] = []
        return context

