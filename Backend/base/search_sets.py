from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod

import numpy as np

from base.exceptions import RouteNotImplemented
from base.object_store import fhir_class_obj
from base.object_store import fhir_resources_route
from dateutil.relativedelta import relativedelta
from typing import Dict, Any
from fhirpy.base.searchset import FHIR_DATE_FORMAT
from datetime import datetime
from fhirpy.lib import SyncFHIRResource

from base.route_converter import get_by_path

CLIENT: SyncFHIRResource


# FHIR_DATE_FORMAT='%Y-%m-%d'

class GetFuncMgmt:
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, strategy: GetFuncInterface = None) -> None:
        """
        First, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> GetFuncInterface:
        """
        The Context maintains a reference to one of the Strategy objects. The
        Context does not know the concrete class of a strategy. It should work
        with all strategies via the Strategy interface.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: GetFuncInterface) -> None:
        """
        Usually, the Context allows replacing a Strategy object at runtime.
        """

        self._strategy = strategy

    def get_data_with_func(self, resources: dict) -> dict:
        """
        2023/05/02 Update: The resources is a dictionary with listed feature key-value pairs.
        e.g.:
        {
            "date": ["2020-12-15", "2020-12-14", "2020-12-13"],
            "value": [87, 87, 87]
        }

        Then, the function will return the result with single date and value based on its strategy.
        e.g.:
        {
            "date": "2020-12-15",
            "value": 87
        }
        """
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        logging.info("Getting patient's data with {} method".format(self._strategy.__name__))
        resource = self._strategy.execute(self._strategy, resources)
        return resource


class GetFuncInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def execute(self, data: dict) -> dict:
        """
        GetFuncInterface 的目的是根據設定(Max, Min, Latest)取得想要的「單筆」資料。
        :param data: dictionary type, 裡面有兩個key: date, value。
                     date的value是一個list，裡面有多個日期；value的value也是一個list，裡面有多個數值。
        :return: dictionary type, 裡面有兩個key: date, value。
                    date的value是一個string，裡面是一個日期；value的value可以是任意的型態，裡面是一個數值
        """
        pass


class GetMax(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        GetMax 的目的是取得時間內最大的資料。需要確定數值是數字型態。

        @param: a dictionary with listed feature key-value pairs
        @return: a dictionary with single feature key-value pairs
        """
        data_date_list = data['date']
        data_value_list = data['value']
        max_index = np.argmax(data_value_list)

        return {"date": data_date_list[max_index], "value": data_value_list[max_index]}


class GetMin(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        GetMin 的目的是取得時間內最小的資料。需要確定數值是數字型態。

        @param: a dictionary with listed feature key-value pairs
        @return: a dictionary with single feature key-value pairs
        """
        data_date_list = data['date']
        data_value_list = data['value']
        min_index = np.argmin(data_value_list)

        return {"date": data_date_list[min_index], "value": data_value_list[min_index]}


class GetLatest(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        GetLatest 的目的是取得最新一筆的資料。

        @param: a dictionary with listed feature key-value pairs
        @return: a dictionary with single feature key-value pairs
        """
        data_date_list = data['date']
        data_value_list = data['value']

        if len(data_date_list) == 0:
            data_date_list.append(None)

        if len(data_value_list) == 0:
            data_value_list.append(None)

        return {"date": data_date_list[0], "value": data_value_list[0]}


class GetAll(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        GetAll 的目的是取得所有的資料。
        :param data:
        :return:
        """
        data_date_list = data['date']
        data_value_list = data['value']

        return {"date": data_date_list, "value": data_value_list}


class ResourceMgmt:
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, strategy: ResourcesInterface | GetValueAndDatetimeInterface = None) -> None:
        """
        First, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> ResourcesInterface | GetValueAndDatetimeInterface:
        """
        The Context maintains a reference to one of the Strategy objects. The
        Context does not know the concrete class of a strategy. It should work
        with all strategies via the Strategy interface.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: ResourcesInterface | GetValueAndDatetimeInterface) -> None:
        """
        Usually, the Context allows replacing a Strategy object at runtime.
        """

        self._strategy = strategy

    def get_data_with_resources(self, patient_id: str,
                                table: Dict, default_time: datetime, data_alive_time=None) -> Dict:
        """
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """

        # ...
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        logging.info("Getting patient's data with {} resources".format(self._strategy.__name__))
        global CLIENT
        CLIENT = fhir_class_obj.client()

        try:
            dict_with_resources = self._strategy.search(self._strategy, patient_id, table, default_time,
                                                        data_alive_time)
        except Exception as e:
            raise e

        return dict_with_resources

    def get_datetime_with_resources(self, resource: Dict or SyncFHIRResource, route: list, default_time: datetime):
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        logging.info("Getting patient data's datetime with {} method".format(self._strategy.__name__))
        resource_time = self._strategy.get_datetime(self._strategy, resource, route, default_time)
        return _return_date_time_formatter(resource_time)

    def get_value_with_resources(self, resource: dict or SyncFHIRResource, route: list):
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        logging.info("Getting patient data's value with the {} method".format(self._strategy.__name__))
        resource_value = self._strategy.get_value(self._strategy, resource, route)
        return resource_value


class ResourcesInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time) -> Dict:
        """
        Search FHIR Resource from FHIR Server and returns the resource list.
        :param patient_id: ID of patient
        :param table: the configuration of the feature that has been defined in the feature table
        :param default_time: The time we default, usually are the time of the prediction (Such as now), but may would be
            used for training.
        :param data_alive_time: The time we want to get the data. If the data is not alive, we will not get the data.
        :return: Dictionary, inside the dictionary are the resources packed into a list and the type of resource.
            resource: list, type: str.capitalize()
        """
        pass


class GetValueAndDatetimeInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def get_datetime(self, resource: dict or SyncFHIRResource, route: list or None, default_time: datetime) -> str:
        """
        Get the datetime of resource. Note that if the resource type is 'Patient', the result would be now.

        :param resource: fhir resource
        :param default_time: The time we default, usually are the time of the prediction (Such as now), but may would be
            used for training.
        :param route: the route of the resource, default is None
        :return: the datetime of the resource or None. The datetime format is YYYY-MM-DDThh:mm
        """
        pass

    @abstractmethod
    def get_value(self, resource: dict or SyncFHIRResource, route: list or None) -> int or str or float or bool:
        """
        Get the value of resource.
        :param resource: fhir resource
        :param route: the route of the resource, default is None. Note that if the resource type is 'Patient',
        the route might be some built-in functions.
        :return: the value of the resource or None
        """

        pass


def _return_date_time_formatter(datetime_string) -> str or None:
    """
        This is a function that returns a standard DateTime format
        While using it, make sure the datetime_string parameter is a valid 'datetime' string
    """

    date_regex = '([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])))'
    date_time_without_sec_regex = '([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[' \
                                  '1-2][0-9]|3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]))) '
    if type(datetime_string) == str:
        if re.search(date_time_without_sec_regex, datetime_string):
            return datetime_string[:16]
        elif re.search(date_regex, datetime_string):
            return datetime_string[:10] + 'T00:00'

    return None


class Observation(ResourcesInterface, GetValueAndDatetimeInterface):
    def search(self,
               patient_id: str,
               table: dict,
               default_time: datetime = datetime.now(),
               data_alive_time=None) -> Dict:
        default_value = table['default_value']

        params = {
            "subject": patient_id,
            "code": table['code'],
        }

        # if data_alive_time is not none, then ignore them
        # Usually used for SMART endpoint.
        if table['data_alive_time'] is not None:
            params['date__ge'] = (default_time - relativedelta(
                years=table['data_alive_time'].get_years(),
                months=table['data_alive_time'].get_months(),
                days=table['data_alive_time'].get_days(),
                hours=table['data_alive_time'].get_hours(),
                minutes=table['data_alive_time'].get_minutes(),
                seconds=table['data_alive_time'].get_seconds()
            )).strftime(FHIR_DATE_FORMAT)

        resources = CLIENT.resources('Observation')
        search = resources.search(
            **params
        ).sort('-date')
        results = search.fetch()

        if len(results) == 0:
            """
            如果resources的長度為0，代表Server裡面沒有這個病患的code data，
            可能是在component-code之中，所以再透過component-code去搜尋
            """
            params_component = params.copy()
            params_component['component_code'] = params_component.pop('code')
            search = resources.search(
                **params_component
            ).sort('-date')
            results = search.fetch()

            if len(results) == 0:
                """
                如果再次搜尋後的結果依舊為0，代表資料庫中沒有此數據，回傳錯誤到前端(可能還可以想一些其他的解決方案)
                """
                results = [default_value]

        return {'resource': results, 'type': 'Observation'}

    def get_datetime(self,
                     resource,
                     route,
                     default_time: datetime = datetime.now()) -> str | None:
        # 很可能是Default的值，或者資料庫根本找不到
        if type(resource) is not dict and type(resource) is not SyncFHIRResource:
            return None

        route_list = []
        if route is None:
            route_list.append(fhir_resources_route.get_route("observation_datetime"))
            route_list.append(fhir_resources_route.get_route("observation_period"))
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None

    def get_value(self, resource, route) -> int or float or str or None:
        # Two situation: one is to get the value of resource, the other is to get the value of resource.component
        if type(resource) is not dict and type(resource) is not SyncFHIRResource:
            return resource

        route_list = []
        if route is None:
            route_list.append(fhir_resources_route.get_route("observation_quantity"))
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))
        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None


class Procedure(ResourcesInterface, GetValueAndDatetimeInterface):

    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time) -> Dict:
        default_value = table['default_value']

        params = {
            "subject": patient_id,
            "code": table['code'],
        }

        # if data_alive_time is not none, then ignore them
        # Usually used for SMART endpoint.
        if table['data_alive_time'] is not None:
            params['date__ge'] = (default_time - relativedelta(
                years=table['data_alive_time'].get_years(),
                months=table['data_alive_time'].get_months(),
                days=table['data_alive_time'].get_days(),
                hours=table['data_alive_time'].get_hours(),
                minutes=table['data_alive_time'].get_minutes(),
                seconds=table['data_alive_time'].get_seconds()
            )).strftime(FHIR_DATE_FORMAT)

        resources = CLIENT.resources('Procedure')
        search = resources.search(
            **params
        ).sort('-date')
        results = search.fetch()

        if len(results) == 0:
            """
            如果再次搜尋後的結果依舊為0，代表資料庫中沒有此數據，回傳錯誤到前端(可能還可以想一些其他的解決方案)
            """
            results = [default_value]

        return {'resource': results, 'type': 'Procedure'}

    def get_datetime(self, resource: dict or SyncFHIRResource, route: list or None, default_time: datetime) \
            -> Any | None:
        if type(resource) is not dict and type(resource) is not SyncFHIRResource:
            return None

        route_list = []
        if route is None:
            route_list.append(fhir_resources_route.get_route("procedure_datetime"))
            route_list.append(fhir_resources_route.get_route("procedure_period"))
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None

    def get_value(self, resource: dict or SyncFHIRResource, route: list or None) -> int or str or float or bool:
        # The default get_value function in Procedure is to return boolean whether the procedure is done or not.
        if resource is None:
            return False

        route_list = []
        if route is None:
            return True
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))
        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None


class Condition(ResourcesInterface, GetValueAndDatetimeInterface):
    def search(self,
               patient_id: str,
               table: dict,
               default_time: datetime = datetime.now(),
               data_alive_time=None) -> Dict:
        params = {
            'subject': patient_id,
            'code': table['code']
        }

        resources = CLIENT.resources('Condition')
        # FIXME: 等等，date__ge呢?
        search = resources.search(
            **params
        ).sort('recorded-date')
        results = search.fetch()

        # 如果result的長度為0，代表病人沒有這個症狀，那就回傳None, 否則回傳結果
        # Consider: 如果這裡不回傳result, 而是回傳true or false，又會如何？
        # Consider: 我有需要回傳整個result list嗎？還是只要回傳一個就好？有什麼情況需要我回傳整個list？計算染疫次數嗎？
        return {'resource': [None] if len(results) == 0 else results, 'type': 'Condition'}

    def get_datetime(self, resource, route, default_time: datetime = datetime.now()) -> str | None:
        route_list = []
        if route is None:
            route_list.append(fhir_resources_route.get_route("condition_datetime"))
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None

    def get_value(self, resource, route: list or None) -> bool or Any:
        # The default get_value function in Condition is to return boolean whether the patient has the conditions.
        if resource is None:
            return False

        route_list = []
        if route is None:
            return True
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        raise ValueError("Can't find the value of condition")


class Patient(ResourcesInterface, GetValueAndDatetimeInterface):
    def search(self,
               patient_id: str,
               table: dict,
               default_time: datetime = datetime.now(),
               data_alive_time=None) -> Dict:
        resources = CLIENT.resources('Patient')
        search = resources.search(_id=patient_id).limit(1)
        patient = search.get()

        return {
            "resource": [patient], 'type': "Patient"
        }

    @staticmethod
    def get_age(resource: dict or SyncFHIRResource, default_time: datetime = datetime.now()) -> int:
        patient_birthdate = datetime.strptime(
            resource.birthDate, FHIR_DATE_FORMAT)
        # If we need to calculate the real age that is 1 year before or so (depends on the default_time)
        # , then calculate it by minus method.
        age = default_time - patient_birthdate
        return int(age.days / 365)

    def get_datetime(self,
                     resource,
                     route,
                     default_time: datetime = datetime.now()) -> str | None:
        """

        :param resource:
        :param default_time:
        :param route:
        :return:
        """
        route_list = []
        if route is None:
            return default_time.strftime("%Y-%m-%d")
        else:
            for item in route:
                route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if get_by_path(resource, item) is not None:
                return get_by_path(resource, item)

        return None

    def get_value(self, resource, route) -> int:
        """

        :param resource:
        :param route:
        :return:
        """

        if type(route) is None:
            raise RouteNotImplemented("Route should not be none, please check the value_route in the feature table")

        route_list = []
        for item in route:
            route_list.append(fhir_resources_route.get_route(item))

        for item in route_list:
            if "()" in item[0]:
                return getattr(self, item[0].replace("()", ""))(resource)
            else:
                if get_by_path(resource, item) is not None:
                    return get_by_path(resource, item)


def get_patient_resources_data_set(patient_id,
                                   table,
                                   default_time: datetime,
                                   data_alive_time=None) -> dict or (dict, dict):
    """
    The function gets the history of patient's resources from the database and return
    :param patient_id: patient's id
    :param table: feature's table,
                  dict type with {'code', 'data_alive_time', 'type_of_data', 'default_value', 'search_type'}
    :param default_time: the time of the default, for model training used. DEFAULT=datetime.now()
    :param data_alive_time: the time range, start from the default_time.
                            e.g. if the data_alive_time is 2 years, and the default_time is not, the server will search
                                 the data that is between now and two years ago
    :return:
            Dict
                {"resource": [SyncFHIRResources...], "component-code": str or None,
                    "type": str(Resource name with capitalized)}
    """

    # 先從FHIR Server取得一系列的病患數據。
    # GetResourceMgmt的全稱是Get Patient Data Resource Management, 為呼叫各種不同FHIR Resources的管理工具
    # 透過obj.strategy設定要找尋的FHIR Resource, 然後使用get_patient_resources()來執行搜尋
    """
    主要有三種不同的Resources: Observation, Condition, Patient

    Observation因為會有component-code的可能，所以相關程式碼會比較複雜
    Condition目前相對單純，就是使用時間大於等於條件與code等於多少就好了
    """

    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(table["type_of_data"]).capitalize()]
    patient_data_dict_origin = patient_resources_mgmt.get_data_with_resources(patient_id,
                                                                              table,
                                                                              default_time,
                                                                              data_alive_time)
    return patient_data_dict_origin


def get_resource_datetime(data: Dict, table: Dict, default_time: datetime = datetime.now()) -> str or None:
    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(data['type']).capitalize()]
    data_datetime = patient_resources_mgmt.get_datetime_with_resources(data["resource"],
                                                                       table['datetime_route'],
                                                                       default_time)
    return data_datetime


def get_resource_value(data: Dict, table: Dict) -> int or float or str or bool:
    # if type(data["resource"]) is not dict and type(data["resource"]) is not SyncFHIRResource:
    #     return data["resource"]

    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(data['type']).capitalize()]
    data_value = patient_resources_mgmt.get_value_with_resources(data["resource"],
                                                                 table['value_route'])
    return data_value


def get_datetime_value_with_func(patient_data_dict: dict, table):
    """
    透過GetXXX的class來取得資料
    :param patient_data_dict: dict, 內有每個feature的date&value
    e.g.: {
               "date": ["2020-12-15", "2020-12-14", "2020-12-13"],
               "value": [87, 87, 87]
           },...
    :param table:

    :return: dict, 內有feature的date&value
    e.g.: {
         "date": "2020-12-15",
         "value": 87
        }
    """
    search_type = str(table['search_type']).capitalize()
    # 沒有輸入search_type的狀況: 如Patient的get_age
    if search_type == '':
        search_type = 'Latest'
    # 如果有輸入Search_type，即會執行GetXXX的class
    try:
        patient_get_setting_mgmt = GetFuncMgmt()
        patient_get_setting_mgmt.strategy = globals()["Get" + search_type]
        patient_resource_result = patient_get_setting_mgmt.get_data_with_func(patient_data_dict)
    except KeyError:
        # 如果沒有支援的search_type，就會raise AttributeError
        raise AttributeError("'{}' search_type is not supported now, check it again.".format(table['search_type']))

    return patient_resource_result
