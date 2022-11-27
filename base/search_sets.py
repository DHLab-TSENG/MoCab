from __future__ import annotations

import configparser
import re
from abc import ABC, abstractmethod
from typing import Dict

from config import configObject as config
from dateutil.relativedelta import relativedelta
from fhirpy import SyncFHIRClient
from fhirpy.base.exceptions import ResourceNotFound
from fhirpy.base.searchset import FHIR_DATE_FORMAT
from fhirpy.base.searchset import datetime
from fhirpy.lib import SyncFHIRResource

CLIENT: SyncFHIRClient = SyncFHIRClient(config['fhir_server']['FHIR_SERVER_URL'])


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
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        print("Getting patient's data with {} method".format(self._strategy.__name__))
        resource = self._strategy.execute(self, resources)
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
        pass


class GetMax(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        For Observation used only, Return the maximum SyncFHIRResources
        @todo: Complete the code.
        @param data:
        @return:
        """
        pass


class GetMin(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        For Observation used only, Return the minimum SyncFHIRResources
        @todo: Complete the code.
        @param data:
        @return:
        """
        pass


class GetLatest(GetFuncInterface):
    def execute(self, data: dict) -> dict:
        """
        GetLatest是每個feature預設的Search Type，所以如果現在是Patient的get_age，也會因為工作流程的關係而需要調用此函式，
        所以要回傳string
        XXX: 或許其實Feature_table可以在Search_Type的部分留白表示不會用到這裡?

        @param data: dict, 因為要配合上面的GetMax & GetMin，可能會需要用到component-code
                     {"resource": list(SyncFHIRResources) or int, "component-code": None or str,
                      "type": "Patient" or "Condition" or "Observation"}
        @return: SyncFHIRResources, int
        """
        data_list = data['resource']
        # Observation and Condition use
        # If Condition data_list is None(代表沒有此病癥), then the data_list type would be None, so it won't be executing
        # the If statement.
        if type(data_list) == list:
            if len(data_list) == 0:
                # TODO: 顯示什麼resources沒有data
                raise Exception("No data inside the data list.")
            # 如果data_list裡面是有資料的，就回傳
            data['resource'] = data_list[0]
        # Patient or Condition with None resources use
        return data


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

        print("Getting patient's data with {} resources".format(self._strategy.__name__))
        global CLIENT
        CLIENT = SyncFHIRClient(config['fhir_server']['FHIR_SERVER_URL'])
        resource_list = self._strategy.search(self, patient_id, table, default_time, data_alive_time)
        return resource_list

    def get_datetime_with_resources(self, data_dictionary: Dict, default_time: datetime):
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        print("Getting patient data's datetime with {} method".format(self._strategy.__name__))
        resource_time = self._strategy.get_datetime(self, data_dictionary, default_time)
        return resource_time

    def get_value_with_resources(self, data_dictionary: Dict):
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        print("Getting patient data's value with the {} method".format(self._strategy.__name__))
        resource_value = self._strategy.get_value(self, data_dictionary)
        return resource_value


class ResourcesInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time=None) -> Dict:
        pass


class GetValueAndDatetimeInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def get_datetime(self, dictionary: dict, default_time: datetime) -> str:
        # dictionary = {'resource': resource, 'component-code': None if type is None else type(str),
        # 'type': 'Observation' or 'Condition' or 'Patient'} 如果給過來的資料並非是object，就直接回傳該數值的time格式
        pass

    @abstractmethod
    def get_value(self, dictionary: dict) -> int or str or float or bool:
        """
        
        如果是Patient，那他的resources放的應該就是integer了，可以直接回傳
        @param dictionary: dict: {'resource': resource, 'component-code': None if type is None else type(str),
        'type': 'Observation' or 'Condition' or 'Patient'} 
        @return: 
        """""

        pass


def _return_date_time_formatter(datetime_string: str) -> str or None:
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
    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time=None) -> Dict:
        data_time_since = (default_time - relativedelta(
            years=table['data_alive_time'].get_years(),
            months=table['data_alive_time'].get_months(),
            days=table['data_alive_time'].get_days(),
            hours=table['data_alive_time'].get_hours(),
            minutes=table['data_alive_time'].get_minutes(),
            seconds=table['data_alive_time'].get_seconds()
        )).strftime(FHIR_DATE_FORMAT)
        code = table['code']
        default_value = table['default_value']

        resources = CLIENT.resources('Observation')
        search = resources.search(
            subject=patient_id,
            date__ge=data_time_since,
            code=code
        ).sort('-date')
        results = search.fetch()
        is_in_component = False

        if len(results) == 0:
            """
            如果resources的長度為0，代表Server裡面沒有這個病患的code data，
            可能是在component-code之中，所以再透過component-code去搜尋
            """

            search = resources.search(
                subject=patient_id,
                date__ge=data_time_since,
                component_code=code
            ).sort('-date')
            results = search.fetch()
            is_in_component = True

            if len(results) == 0:
                """
                如果再次搜尋後的結果依舊為0，代表資料庫中沒有此數據，回傳錯誤到前端(可能還可以想一些其他的解決方案)
                """
                if default_value is None:
                    raise ResourceNotFound(
                        'Could not find the resources {code} under time {time}, no enough data for the patient'.format(
                            code=code,
                            time=data_time_since
                        )
                    )
                else:
                    results = default_value

        return {'resource': results, 'component_code': code if is_in_component else None,
                'type': 'Observation'}

    def get_datetime(self, dictionary: dict, default_time) -> str | None:
        try:
            return _return_date_time_formatter(dictionary['resource'].effectiveDateTime)
        except (AttributeError, KeyError):
            try:
                return _return_date_time_formatter(dictionary['resource'].effectivePeriod.start)
            except (AttributeError, KeyError):
                return None

    def get_value(self, dictionary: dict) -> int | str:
        # Two situation: one is to get the value of resource, the other is to get the value of resource.component
        if type(dictionary['resource']) != SyncFHIRResource:
            return dictionary['resource']

        if dictionary['component_code'] is not None:
            for component in dictionary['resource'].component:
                for coding in component.code.coding:
                    if coding.code == dictionary['component_code']:
                        return component.valueQuantity.value
        else:
            try:
                return dictionary['resource'].valueQuantity.value
            except KeyError:
                return dictionary['resource'].valueString


class Condition(ResourcesInterface, GetValueAndDatetimeInterface):
    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time=None) -> Dict:
        code = table['code']

        resources = CLIENT.resources('Condition')
        # FIXME: 等等，date__ge呢?
        search = resources.search(
            subject=patient_id,
            code=code
        ).sort('recorded-date')
        results = search.fetch()

        # 如果result的長度為0，代表病人沒有這個症狀，那就回傳None, 否則回傳結果
        # Consider: 如果這裡不回傳result, 而是回傳true or false，又會如何？
        # Consider: 我有需要回傳整個result list嗎？還是只要回傳一個就好？有什麼情況需要我回傳整個list？計算染疫次數嗎？
        return {'resource': None if len(results) == 0 else results, 'component_code': None,
                'type': 'Condition'}

    def get_datetime(self, dictionary: dict, default_time) -> str | None:
        try:
            return _return_date_time_formatter(dictionary['resource'].recordedDate)
        except AttributeError:
            return None

    def get_value(self, dictionary: dict) -> bool:
        return False if dictionary['resource'] is None else True


class Patient(ResourcesInterface, GetValueAndDatetimeInterface):
    def search(self, patient_id: str, table: dict, default_time: datetime, data_alive_time=None) -> Dict:
        resources = CLIENT.resources('Patient')
        search = resources.search(_id=patient_id).limit(1)
        patient = search.get()

        result = None
        if table['code'] == 'age':
            result = getattr(self._strategy, "get_{}".format(str(table['code']).lower()))(patient, default_time)
        return {
            "resource": result, "component_code": None, 'type': "Patient"
        }

    @staticmethod
    def get_age(patient: SyncFHIRResource, default_time) -> int:
        patient_birthdate = datetime.datetime.strptime(
            patient.birthDate, FHIR_DATE_FORMAT)
        # If we need to calculate the real age that is 1 year before or so (depends on the default_time)
        # , then calculate it by minus method.
        age = default_time - patient_birthdate
        return int(age.days / 365)

    def get_datetime(self, dictionary: dict, default_time) -> str:
        """
        直接Return datetime format就好
        @param dictionary:
        @param default_time:
        @return:
        """
        return default_time.strftime("%Y-%m-%d")

    def get_value(self, dictionary: dict) -> int:
        """
        直接Return就好
        @param dictionary:
        @return:
        """
        if type(dictionary['resource']) is int:
            return dictionary['resource']


def get_patient_resources(patient_id, table, default_time: datetime, data_alive_time=None) -> dict:
    """
    The function will get the patient's resources from the database and return
    :param patient_id: patient's id
    :param table: feature's table,
                  dict type with {'code', 'data_alive_time', 'type_of_data', 'default_value', 'search_type'}
    :param default_time: the time of the default, for model training used. DEFAULT=datetime.now()
    :param data_alive_time: the time range, start from the default_time.
                            e.g. if the data_alive_time is 2 years, and the default_time is not, the server will search
                                 the data that is between now and two years ago
    :return: Dict, {"resource": SyncFHIRResources, "component-code": str or None,
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
    patient_data_dict = patient_resources_mgmt.get_data_with_resources(patient_id, table, default_time, data_alive_time)

    # 然後再根據不同的欲取得的資料設定(如最新的資料, 最大的資料, 最小的資料...)來從data_list中取得符合設定的data
    # 該設定可以在features.csv中的search_type column設定

    """
    主要會有四種不同的設定: NULL, latest, min, max
    latest為取得最新的資料, min為取得資料集中，數值最小的資料, max為取得資料集中，數字最大的資料, 
    NULL就是不做任何處置，會使用這個設定的數值有Patient age，
    因為在Patient resources中，age會直接計算出年齡並回傳結果，所以不用再取得數值了
    """
    search_type = str(table['search_type']).capitalize()

    # 沒有輸入search_type的狀況: 如Patient的get_age
    if search_type == "":
        patient_resource_result = patient_data_dict
    # 如果有輸入search_type，檢查是不是latest, min or max
    # XXX: 希望能是寫活的，可以自動判別目前已經開發出來的Concrete getFuncInterface
    elif search_type in ('Latest', 'Min', 'Max'):
        patient_get_setting_mgmt = GetFuncMgmt()
        patient_get_setting_mgmt.strategy = globals()["Get" + search_type]
        patient_resource_result = patient_get_setting_mgmt.get_data_with_func(patient_data_dict)
    else:
        raise AttributeError("'{}' search_type is not supported now, check it again.".format(table['search_type']))

    return patient_resource_result


def get_resource_datetime(data: Dict, default_time: datetime) -> str | None:
    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(data['type']).capitalize()]
    data_datetime = patient_resources_mgmt.get_datetime_with_resources(data, default_time)
    return data_datetime


def get_resource_value(data: Dict) -> int or float or str or bool:
    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(data['type']).capitalize()]
    data_value = patient_resources_mgmt.get_value_with_resources(data)
    return data_value


def get_resource_datetime_and_value(data: Dict, default_time: datetime) -> (str or None, int or float or str or bool):
    patient_resources_mgmt = ResourceMgmt()
    patient_resources_mgmt.strategy = globals()[str(data['type']).capitalize()]
    data_datetime = patient_resources_mgmt.get_datetime_with_resources(data, default_time)
    data_value = patient_resources_mgmt.get_value_with_resources(data)
    return data_datetime, data_value


if __name__ == "__main__":
    import os
    os.chdir("../")
    from feature_table import feature_table

    features__table = feature_table
    patient__id = "test-03121002"
    feature__table = features__table.get_model_feature_dict('nsti')
    default_time = datetime.datetime.now()

    patient_result_dict = dict()
    for key in feature__table:
        patient_result_dict[key] = \
            get_patient_resources(patient_id=patient__id, table=feature__table[key], default_time=default_time)
        print(patient_result_dict[key])

    for key in patient_result_dict:
        print(key, get_resource_datetime_and_value(patient_result_dict[key], default_time))
