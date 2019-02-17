import requests
import os.path
import json
import time


class Info:

    @staticmethod
    def start_operation(operation, message):
        print(f'"{operation}"' + message)

    @staticmethod
    def end_operation(operation):
        print(f'"{operation}" => Успешно!')

    @staticmethod
    def warning(operation, message):
        print(f"{operation}.", message)

    @staticmethod
    def error(message, operation):
        print(f'Ошибка! Метод "{operation}".')
        print(message)


class User:
    def __init__(self, user_name, api_v='', token=''):
        self.__short_name = user_name if user_name.isalpha() else ''
        self.__id = user_name if user_name.isdigit() else None
        self.__first_name = ''
        self.__last_name = ''
        self.__api_v = api_v
        self.__token = token
        self.__api_url = r'https://api.vk.com/method/'
        self.__friends = []
        self.__groups = []
        self.__friends_groups = []
        self.__groups_info = []
        self.__file = 'groups.json'

    def __get_params(self):
        """ Основные параметры запроса """
        return {'v': self.__api_v, 'access_token': self.__token}

    def __get_data(self, method='users.get', **user__params):
        """ Обработка пользовательских запросов """
        params = self.__get_params()
        url = os.path.join(self.__api_url, method)

        for param in user__params:
            params[param] = user__params[param]

        return requests.get(url, params=params).json()

    def __get_user(self):
        """ Получение данных пользователя по его короткому имени или id """
        if self.__short_name:
            data = self.__get_data(**{'user_ids': self.__short_name})

            try:
                self.__id = data['response'][0]['id']
                self.__first_name = data['response'][0]['first_name']
                self.__last_name = data['response'][0]['last_name']

            except KeyError as e:
                Info.error(f'Ключ {e} не найден!', self.__get_user.__name__)

        elif self.__id:
            data = self.__get_data(**{'user_ids': self.__id})

            try:
                self.__first_name = data['response'][0]['first_name']
                self.__last_name = data['response'][0]['last_name']

            except KeyError as e:
                Info.error(f'Ключ {e} не найден!', self.__get_user.__name__)

        else:
            Info.error(f'Ошибка входных данных!', self.__get_user.__name__)

    def __get_friends(self):
        """ Получение списка идентификаторов друзей пользователя """
        if self.__id:

            data = self.__get_data('friends.get', **{'user_id': self.__id})

            try:
                self.__friends = data['response']['items']

            except KeyError as e:
                Info.error(f' {e} не обнаружен!', self.__get_friends.__name__)

        else:
            Info.error('Отсутствующий ID!', self.__get_friends.__name__)

    def __get_friends_groups(self):
        """ Получение списка идентификаторов групп пользователей """
        if self.__friends:
            for friend in self.__friends:
                try:
                    Info.start_operation('Запрос данных', '.' * 12)
                    response = self.__get_data('groups.get', **{'user_id': friend})
                    self.__friends_groups.extend(response['response']['items'])
                    Info.end_operation('Запрос данных')
                    time.sleep(0.4)

                except KeyError:
                    Info.error(
                        f'{friend} (заблокирована или удалена)',
                        self.__get_friends_groups.__name__)
                    continue
            self.__friends_groups = list(set(self.__friends_groups))
        else:
            Info.error(
                'Список друзей не обнаружен!',
                self.__get_friends_groups.__name__)

    def __get_user_groups(self):
        """ Получение списка идентификаторов групп нашего пользователя """
        if self.__id:

            data = self.__get_data('groups.get', **{'user_id': self.__id})

            try:
                self.__groups = data['response']['items']

            except KeyError as e:
                Info.error(f'{e} не обнаружен!', self.__get_user_groups.__name__)

        else:
            Info.error('Отсутствующий ID!', self.__get_user_groups.__name__)

    def __get_groups_info(self, groups):
        """ Получение информации о группах """
        if not groups:
            return []

        groups = ', '.join([str(group) for group in groups])
        response = self.__get_data('groups.getById', **{'group_ids': groups, 'fields': 'members_count'})
        try:
            groups_info = response['response']

            for group in groups_info:
                grup_dict = {'Название группы:': group['name']}
                grup_dict['ID группы:'] = group['id']
                grup_dict['Количество участников:'] = group['members_count']
                grup_dict['Ник:'] = group['screen_name']
                self.__groups_info.append(grup_dict)

        except KeyError as e:
            Info.error(f'Ключ {e} не найден!', self.__get_groups_info.__name__)

    def __get_unique_groups(self):
        """ Получение информации о уникальных группах пользователя"""
        if self.__groups and self.__friends_groups:
            unique_groups = set(self.__groups).difference(set(self.__friends_groups))
            self.__get_groups_info(unique_groups)
        else:
            Info.error(
                'Нет данных для получения уникальных групп!',
                self.__get_unique_groups.__name__)

    def __export(self):
        """ Сохранение данных о пользователе и его уникальных группах в файл """
        if self.__groups_info:
            user_data = {
                'Имя пользователя': self.__first_name,
                'Фамилия пользователя': self.__last_name,
                'ID ВКонтакте': self.__id,
                'Список уникальных групп': self.__groups_info,
            }

            with open(self.__file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=4, ensure_ascii=False)
        else:
            Info.warning(
                'Нет данных для записи',
                'Отсутствуют уникальные группы!')

    def run(self):
        self.__get_user()
        self.__get_friends()
        self.__get_user_groups()
        self.__get_friends_groups()
        self.__get_unique_groups()
        self.__export()


def main():
    token = '6fdac1e31f0b8be45f450183099cdc9233d11c490ae96cd4843731a6715b362bdb254e6bdafa2d01fa1c5'

    api_v = '5.92'

    user_choice = input('Введите имя пользователя или его ID:')

    user = User(user_choice, api_v=api_v, token=token)

    user.run()


if __name__ == '__main__':
    main()
