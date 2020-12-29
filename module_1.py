#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from datetime import date
import logging
import sys
from typing import List
import xml.etree.ElementTree as ET


class IllegalYearError(Exception):
    def __init__(self, year, message="Illegal year number"):
        self.year = year
        self.message = message

        super(IllegalYearError, self).__init__(message)

    def __str__(self):
        return f"{self.year} -> {self.message}"


class UnknownCommandError(Exception):
    def __init__(self, command, message="Unknown command"):
        self.command = command
        self.message = message
        super(UnknownCommandError, self).__init__(message)

    def __str__(self):
        return f"{self.command} -> {self.message}"


@dataclass(frozen=True)
class Worker:
    name: str
    post: str
    year: int


@dataclass
class Staff:
    workers: List[Worker] = field(default_factory=lambda: [])

    def add(self, name: str, post: str, year: int) -> None:
        today = date.today()

        if year < 0 or year > today.year:
            raise IllegalYearError(year)

        self.workers.append(
            Worker(
                name=name,
                post=post,
                year=year
            )
        )

        self.workers.sort(key=lambda worker: worker.name)

    def __str__(self) -> str:

        table = []
        line = '+-{}-+-{}-+-{}-+-{}-+'.format(
            '-' * 4,
            '-' * 30,
            '-' * 20,
            '-' * 8
        )
        table.append(line)
        table.append(
            '| {:^4} | {:^30} | {:^20} | {:^8} |'.format(
                "№",
                "Ф.И.О.",
                "Должность",
                "Год"
            )
        )
        table.append(line)

        for idx, worker in enumerate(self.workers, 1):
            table.append(
                '| {:>4} | {:<30} | {:<20} | {:>8} |'.format(
                    idx,
                    worker.name,
                    worker.post,
                    worker.year
                )
            )
            table.append(line)
            return '\n'.join(table)

    def select(self, period: int) -> List[Worker]:

        today = date.today()
        result = []
        for worker in self.workers:
            if today.year - worker.year >= period:
                result.append(worker)

        return result

    def load(self, filename) -> None:
        with open(filename, 'r', encoding='utf8') as fin:
            xml = fin.read()

        parser = ET.XMLParser(encoding="utf8")
        tree = ET.fromstring(xml, parser=parser)

        self.workers = []
        for worker_element in tree:
            name, post, year = None, None, None

            for element in worker_element:
                if element.tag == 'name':
                    name = element.text
                elif element.tag == 'post':
                    post = element.text
                elif element.tag == 'year':
                    year = int(element.text)
                if name is not None and post is not None \
                        and year is not None:
                    self.workers.append(
                        Worker(
                            name=name,
                            post=post,
                            year=year
                        )
                    )

    def save(self, filename) -> None:
        root = ET.Element('workers')

        for worker in self.workers:
            worker_element = ET.Element('worker')

            name_element = ET.SubElement(worker_element, 'name')
            name_element.text = worker.name

            post_element = ET.SubElement(worker_element, 'post')
            post_element.text = worker.post

            year_element = ET.SubElement(worker_element, 'year')
            year_element.text = str(worker.year)

            root.append(worker_element)

        tree = ET.ElementTree(root)
        with open(filename, 'wb') as fout:
            tree.write(fout, encoding='utf8', xml_declaration=True)


if __name__ == '__main__':
    logging.basicConfig(
        filename='workers.log',
        level=logging.INFO
    )

    staff = Staff()

    while True:
        try:
            command = input(">>> ").lower()

            if command == 'exit':
                break

            elif command == 'add':
                name = input("Фамилия и инициалы? ")
                post = input("Должность? ")
                year = int(input("Год поступления? "))

                staff.add(name, post, year)
                logging.info(
                    f"Добавлен сотрудник: {name}, {post}, "
                    f"поступивший в {year} году."
                )

            elif command == 'list':
                print(staff)
                logging.info("Отображен список сотрудников.")

            elif command.startswith('select '):
                parts = command.split(maxsplit=1)
                selected = staff.select(parts[1])

                if selected:
                    for idx, worker in enumerate(selected, 1):
                        print(
                            '{:>4}: {}'.format(idx, worker.name)
                        )
                    logging.info(
                        f"Найдено {len(selected)} работников со "
                        f"стажем более {parts[1]} лет."
                    )

                else:
                    print("Работники с заданным стажем не найдены.")
                    logging.warning(
                        f"Работники со стажем более {parts[1]} лет не найдены."
                    )

            elif command.startswith('load '):
                parts = command.split(maxsplit=1)
                staff.load(parts[1])
                logging.info(f"Загружены данные из файла {parts[1]}.")

            elif command.startswith('save '):
                parts = command.split(maxsplit=1)
                staff.save(parts[1])
                logging.info(f"Сохранены данные в файл {parts[1]}.")

            elif command == 'help':
                print("Список команд:\n")
                print("add - добавить работника;")
                print("list - вывести список работников;")
                print("select <стаж> - запросить работников со стажем;")
                print("load <имя_файла> - загрузить данные из файла;")
                print("save <имя_файла> - сохранить данные в файл;")
                print("help - отобразить справку;")
                print("exit - завершить работу с программой.")

            else:
                raise UnknownCommandError(command)

        except Exception as exc:
            logging.error(f"Ошибка: {exc}")
            print(exc, file=sys.stderr)