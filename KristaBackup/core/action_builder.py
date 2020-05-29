# -*- encoding: utf-8 -*-

import copy
import logging

from common import schemes
from core.actions import action_types
from core.actions import MoveBkpPeriod


class ActionBuilder:
    """Строитель действий.

    Attributes:
        actions_records: Словарь с исходными конфигурациями.
        _built_records: Словарь с готовыми конфигурациями действий.

    """

    def __init__(self, actions_records):
        """

        Args:
            actions_records: Первичная конфигурация всех действий.

        """
        self.logger = logging.getLogger()
        self.actions_records = actions_records
        self._built_records = {}
        self._built_actions = {}

    def __call__(self, action_name):
        """Создает и конфигурирует действие.

        Args:
            action_name: Строка, имя действия.

        Returns:
            Action или None, если не удалось создать/сконфигурировать
                действие.

        """
        if action_name in self._built_actions:
            return self._built_actions.get(action_name)
        action_conf = self.assemble_attributes(action_name)
        if not action_conf:
            self.logger.warning(
                'Отсутствует описание для действия %s',
                action_name,
            )
            return None

        if 'type' not in action_conf.keys():
            self.logger.error(
                'Отсутствует тип действия %s',
                action_name,
            )
            return None

        # В зависимости от типа в конфиге создаем объект заданного типа
        action_cls = action_types.get(action_conf['type'])
        if action_cls is None:
            self.logger.error(
                'Неопознанный тип действия %s в конфигурации задания %s',
                action_conf['type'],
                action_name,
            )
            return None

        action = action_cls(action_name)
        self.logger.debug('Конфигурирование действия %s', action_name)
        self.configure_action(action, action_conf)
        self.logger.info(
            'Сконфигурировано действие %s',
            action_name,
        )
        self.logger.debug('%s', action)

        self._built_actions[action_name] = action
        return action

    def assemble_attributes(self, action_name):
        """Формирует конфигурацию действия.

        1) Берёт исходную конфигурацию.
        2) Наследует атрибуты предка из source.

        Args:
            action_name: Строка, имя действия.

        Returns:
            Словарь с конфигурацией.

        """
        if action_name in self._built_records:
            return self._built_records.get(action_name)

        prime_action_conf = self.actions_records.get(action_name)
        return self._assemble_attributes(
            action_name,
            prime_action_conf,
        )

    def _assemble_attributes(
        self,
        action_name,
        action_config,
        history=None,
    ):
        """Собирает словарь с атрибутами действия.

        Args:
            action_name: Строка, имя действия.
            action_config: Словарь с атрибутами формируемого действия.
            history: Множество с предками действия.

        Returns:
            Словарь с атрибутами

        """
        history = history or set()

        if 'source' in action_config:
            ancestor_name = action_config.get('source')
            if ancestor_name in history:
                raise AttributeError(
                    'Рекурсивное наследование действий: {0}'.format(history),
                )
            history.add(ancestor_name)

            if ancestor_name in self._built_records:
                ancestor_config = self._built_records.get(ancestor_name)
            else:
                ancestor_config = self.actions_records.get(ancestor_name)
                if not ancestor_config:
                    self.logger.error(
                        'Отсутствует действие %s, которое является предком',
                        ancestor_name,
                    )
                    return None
                ancestor_config = self._assemble_attributes(
                    ancestor_name,
                    ancestor_config,
                    history,
                )
        else:
            ancestor_config = {}

        for attribute in ancestor_config:
            if attribute not in action_config:
                action_config[attribute] = copy.copy(
                    ancestor_config[attribute],
                )

        self._built_records[action_name] = action_config
        return action_config

    def _assemble_action_list(self, action_list):
        result = []
        for action_name in action_list:
            action = self(action_name)
            result.append(action)
        return result

    def configure_action(self, action_obj, action_conf):
        """Устанавливает значение объекту action_obj на основе action_conf.

        Большинство атрибутов из action_conf просто присваиваются
        соответствующим атрибутам action_obj. Но:

        1. Если атрибут из action_obj это лист, то атрибут из action_conf
            конвертируется в строку и разбивается по запятым (если он не лист).
        2. По naming_scheme объекту action_obj присваивается атрибут scheme со
            схемой с соответствующим scheme_id.
        3. Атрибуту source делается подстановка соответствующего реального действия.

        Args:
            action_obj: Объект потомка Action.
            action_conf: Словарь с конфигурацией.

        """
        self._update_source_action_conf(action_conf)
        self._update_scheme_action_conf(action_conf)
        if isinstance(action_obj, MoveBkpPeriod):
            self._update_action_list_action_conf(action_conf)

        for attribute_name in action_conf:
            attr_value = action_conf[attribute_name]

            attr = getattr(action_obj, attribute_name, None)
            if isinstance(attr, list):
                if not isinstance(action_conf[attribute_name], list):
                    attr_value = str(action_conf[attribute_name])
                    attr_value = [
                        a_value.strip()
                        for a_value in attr_value.split(',')
                    ]
            setattr(action_obj, attribute_name, attr_value)

    def _update_source_action_conf(self, action_conf):
        source_name = action_conf.get('source')
        if self._built_records.get(source_name, {}).get('type'):
            # У предка есть тип, его нужно создать.
            self.logger.debug(
                'Требуется предок %s',
                source_name,
            )
            source = self(source_name)
            action_conf['source'] = source
        else:
            action_conf['source'] = None

    def _update_action_list_action_conf(self, action_conf):
        action_list = action_conf.get('action_list')
        if action_list and action_conf:
            _action_list = self._assemble_action_list(action_list)
            action_conf['action_list'] = _action_list

    def _update_scheme_action_conf(self, action_conf):
        scheme = action_conf.setdefault('naming_scheme', None)
        if isinstance(scheme, dict):
            action_conf['scheme'] = schemes.get_scheme_by_config(scheme)
        else:
            action_conf['scheme'] = schemes.get_scheme(scheme)
