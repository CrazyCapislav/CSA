import json
import logging
import sys
import isa
from src.machine_modules.DataPath import DataPath
from src.machine_modules.MemoryConfiguratour import MemoryConfigurator
from src.machine_modules.MUX import *

import json
import logging
import sys
import isa
from src.machine_modules.DataPath import DataPath
from src.machine_modules.MemoryConfiguratour import MemoryConfigurator
from src.machine_modules.MUX import *

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ControlUnit:
    def __init__(self, program, data_path, max_ticks=100000):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0  # Счётчик тактов
        self.max_ticks = max_ticks  # Максимальное количество тиков
        logging.info("Control Unit initialized.")

    def tick(self):
        """Продвигаем модельное время вперед на один такт"""
        self._tick += 1
        logging.info({self})

        # Проверяем, достигнуто ли максимальное количество тиков
        if self._tick >= self.max_ticks:
            logging.info(f"Maximum tick count {self.max_ticks} reached. Halting execution.")
            raise StopIteration()

    def decode_and_execute_control_flow_instruction(self, instr, opcode):
        """Декодировать и выполнить инструкцию управления потоком исполнения."""
        logging.info(f"Executing control flow instruction: {opcode} at PC: {self.program_counter}")

        if opcode == 'hlt':
            logging.info("HLT instruction encountered. Halting execution.")
            raise StopIteration()

        elif opcode == 'jmp':
            addr = instr["addr"]
            logging.info(f"JMP to address: {addr}")
            self.program_counter = addr
            self.tick()
            return True

        elif opcode == 'je':
            addr = instr["addr"]
            if self.data_path.zero_flag:
                logging.info(f"JE condition met. Jumping to address: {addr}")
                self.program_counter = addr
                self.tick()
            else:
                logging.info(f"JE condition not met. Incrementing PC.")
                self.program_counter += 1
            self.tick()
            return True
        elif opcode == 'jne':
            addr = instr["addr"]
            if not self.data_path.zero_flag:
                logging.info(f"JNE condition met.Jumping to address: {addr} ")

                self.program_counter = addr
            else:
                logging.info(f"JNE condition not met. Incrementing PC.")
                self.program_counter += 1
                self.tick()
            self.tick()
            return True
        elif opcode == 'jb':
            addr = instr["addr"]
            if self.data_path.negative_flag:
                logging.info(f"JB condition met. Jumping to address: {addr}")
                self.program_counter = addr
                self.tick()
            else:
                logging.info(f"JB condition not met. Incrementing PC.")
                self.program_counter += 1
            self.tick()
            return True


        return False

    def decode_and_execute_instruction(self):
        """Основной цикл процессора. Декодирует и выполняет инструкцию."""
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        logging.info(f"Decoding instruction at PC: {self.program_counter} - Opcode: {opcode}")

        # Проверка инструкций управления потоком
        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return

        # Обработка остальных инструкций
        if opcode == "ld":
            logging.info(f"Executing LD instruction. Address mode: {instr['addr_mode']}")
            if instr["addr_mode"] == "direct":
                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.info(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Проверка ввода
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                # Загружаем данные в аккумулятор из памяти
                self.data_path.latch_acc("MEM")
                logging.info(f"Loaded data into accumulator from memory.")
                self.tick()

                # Увеличиваем программный счётчик
                self.program_counter += 1
                self.tick()
            elif instr["addr_mode"] == "indirect":

                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.info(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Загружаем значение из памяти в регистр данных
                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()

                # Переключаем адрес на значение из регистра данных
                self.data_path.latch_da("DR", self.data_path.data_register)
                logging.info(f"Latching data address from DR: {self.data_path.data_register}")
                self.tick()

                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                    self.data_path.latch_acc("MEM")
                    self.data_path.data_memory[self.data_path.input_adr] = self.data_path.input_adr
                    self.tick()
                else:
                    # Загружаем данные в аккумулятор из памяти
                    self.data_path.latch_acc("MEM")
                    logging.info(f"Loaded data into accumulator from memory.")
                    self.tick()

                # Увеличиваем программный счётчик
                self.program_counter += 1
                self.tick()

        elif opcode == "st":
            logging.info(f"Executing ST instruction. Address mode: {instr['addr_mode']}")
            if instr["addr_mode"] == "direct":
                self.data_path.latch_da("CU", instr["addr"])
                logging.info(f"Latching data address for store: {instr['addr']}")
                self.tick()

                self.data_path.write_to_memory()
                logging.info(f"Stored accumulator data into memory at address {self.data_path.data_address}.")
                self.data_path.check_output()

                self.tick()
                self.program_counter += 1
                self.tick()
            if instr["addr_mode"] == "indirect":
                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.info(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Загружаем значение из памяти в регистр данных
                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()

                # Переключаем адрес на значение из регистра данных
                self.data_path.latch_da("DR", self.data_path.data_register)
                logging.info(f"Latching data address from DR: {self.data_path.data_register}")
                self.tick()

                self.data_path.write_to_memory()
                logging.info(f"Stored accumulator data into memory at address {self.data_path.data_address}.")
                self.data_path.check_output()

                self.tick()
                self.program_counter += 1
                self.tick()

        elif opcode == "cmp":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.program_counter += 1
                self.tick()
            if instr["addr_mode"] == "indirect":
                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.info(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Загружаем значение из памяти в регистр данных
                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()

                # Переключаем адрес на значение из регистра данных
                self.data_path.latch_da("DR", self.data_path.data_register)
                logging.info(f"Latching data address from DR: {self.data_path.data_register}")
                self.tick()

                # Проверка ввода
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                # Загружаем данные в аккумулятор из памяти

                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.program_counter += 1
                self.tick()

            if instr["addr_mode"] == "direct":

                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.info(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Проверка ввода
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                # Загружаем данные в аккумулятор из памяти

                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.program_counter += 1
                self.tick()
        elif opcode == "inc":
            self.data_path.latch_acc("NONE")
            self.tick()
            self.data_path.alu_inc()
            self.tick()
            self.program_counter += 1
            self.tick()
        elif opcode == "add":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_add()
                self.tick()
                self.program_counter += 1
                self.tick()
            if instr["addr_mode"] == "indirect":
                self.data_path.latch_da("CU", instr["addr"])
                self.tick()

                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                # Загружаем данные в аккумулятор из памяти
                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()
                self.data_path.latch_da("DR", self.data_path.data_register)
                self.tick()
                self.data_path.latch_dr("MEM", self.data_path.data_memory[self.data_path.data_address])
                self.tick()
                self.data_path.alu_add()
                self.tick()
                self.program_counter += 1
                self.tick()
        elif opcode == "mod":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_mod()
                self.tick()
                self.program_counter += 1
                self.tick()

    def run(self):
        """Запускает выполнение программы"""
        logging.info("Starting program execution.")
        try:
            while self.program_counter < len(self.program):
                self.decode_and_execute_instruction()
                logging.info(f"Control Unit state: {self}")
        except StopIteration:
            logging.info("Program halted.")

        # Формируем одну строку из output_buffer
        output_string = ''.join(str(i) for i in self.data_path.output_buffer)

        # Обрезаем последние нули

        # Выводим содержимое output_buffer
        logging.info(f"Program finished. Output buffer contents: {output_string}")
        print(f"Output: {output_string}")

    def __repr__(self):
        return "{{TICK: {}, PC: {}, ADDR: {}, ACC: {}, DR: {}, DA: {}}}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.acc,
            self.data_path.data_register,
            self.data_path.data_address,
        )


def main():
    input_json_file = 'output_compiler.json'
    output_json_file = 'output_compiler_memory.json'

    # Инициализируем MemoryConfigurator для обработки JSON данных
    configurator = MemoryConfigurator(input_json_file)
    configurator.save_data_to_json(output_json_file)
    configurator.save_instructions_to_json('output_instructions.json')

    input_string_1 = 'catcatcat\0.dogo\0.$.'

    input_buffer = list(input_string_1)
    print(f"Input buffer: {input_buffer}")

    # Инициализация DataPath с использованием файла output_compiler_memory.json
    data_path = DataPath('output_compiler_memory.json', input_buffer)

    # Чтение инструкций программы из JSON-файла
    with open('output_instructions.json', 'r') as file:
        program = json.load(file)["instructions"]  # Предполагаем, что инструкции хранятся под ключом "instructions"

    # Инициализация ControlUnit и запуск программы
    control_unit = ControlUnit(program, data_path)
    control_unit.run()


if __name__ == '__main__':
    main()
