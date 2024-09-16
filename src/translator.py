import os

from src.machine import MemoryConfigurator
from src.translator_modules.ast_nodes import *
from src.translator_modules.code_generator import CodeGenerator
from src.translator_modules.compiler import Compiler
from src.translator_modules.lexer import lex
from src.translator_modules.parser import Parser


def main():
    code3123 = '''
        {
            print("Hello world!");
        }
        '''
    code32131 = '''
    {
        string str = input();
        while(str != "$"){
            print(str);
            str = input();
        }
    }
    '''
    code3123 = '''
        {   
            string username = input();
            print("Hello, ");
            print(username);
        }
        '''
    code3213 = '''
            {
                int i = 0;
                int sum = 0;
                while(i < 1000){
                    if(i % 3 == 0){
                        sum = sum + i;
                    }
                    else{
                        if(i % 5 == 0){
                            sum = sum + i;
                        }
                    }
                    i = i + 1;
                }
                print(sum);
            }
            '''
    code = '''
                {
                    print("Hello world!");
                    string username = input();
                    print("Hello, ");
                    print(username);
                    int i = 0;
                    int sum = 0;
                    while(i < 1000){
                        if(i % 3 == 0){
                            sum = sum + i;
                        }
                        else{
                            if(i % 5 == 0){
                                sum = sum + i;
                            }
                        }
                        i = i + 1;
                    }
                    print(sum);
                    string str = input();
                    while(str != "$"){
                        print(str);
                        str = input();
                    }
                }
                '''

    code54 = '''
                {
                    int i = 0;
                    while(i < 1000){
                        i = i + 1;
                    }
                    print(i);
                }
                '''

    # Запуск лексера
    tokens = lex(code)

    # Запуск парсера
    parser = Parser(tokens)
    ast = parser.parse()

    # Вывод AST для отладки
    save_ast_to_file(ast, 'ast_output.txt')

    # Запуск генератора
    generator = CodeGenerator()
    generator.generate(ast)
    generator.save_to_file()

    compiler = Compiler("output_code.json")
    os.makedirs("output", exist_ok=True)
    compiler.save_unified_json("output_compiler.json")

    input_json_file = 'output_compiler.json'  # Укажите путь к вашему исходному JSON-файлу
    output_json_file = 'output_compiler_memory.json'  # Укажите путь к выходному JSON-файлу

    configurator = MemoryConfigurator(input_json_file)

    # Сохранение данных в новый JSON-файл
    configurator.save_data_to_json(output_json_file)
    configurator.save_instructions_to_json('output_instructions.json')


def save_ast_to_file(node, filename):
    """Сохраняет AST в файл"""
    ast_output = []

    def print_ast(ast_node, indent=""):
        """Функция для сохранения AST в список"""
        if isinstance(ast_node, ProgramNode):
            ast_output.append(indent + "Program:")
            for stmt in ast_node.statements:
                print_ast(stmt, indent + "  ")
        elif isinstance(ast_node, PrintNode):
            ast_output.append(indent + "Print:")
            print_ast(ast_node.expression, indent + "  ")
        elif isinstance(ast_node, VariableAssignNode):
            ast_output.append(indent + f"Assign(var={ast_node.var_name}, var_type={ast_node.var_type})")
            print_ast(ast_node.expression, indent + "  ")
        elif isinstance(ast_node, WhileNode):
            ast_output.append(indent + "While:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  WhileBody:")
            for stmt in ast_node.body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, IfNode):
            ast_output.append(indent + "If:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  Body:")
            for stmt in ast_node.body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, IfElseNode):
            ast_output.append(indent + "IfElse:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  IfBody:")
            for stmt in ast_node.if_body:
                print_ast(stmt, indent + "    ")
            ast_output.append(indent + "  ElseBody:")
            for stmt in ast_node.else_body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, BinaryOpNode):
            # Форматируем вывод для бинарных операций с правильными отступами
            ast_output.append(indent + "BinaryOp(")
            print_ast(ast_node.left, indent + "    ")
            ast_output.append(indent + f"  {ast_node.operator}")
            print_ast(ast_node.right, indent + "    ")
            ast_output.append(indent + ")")
        elif isinstance(ast_node, NumberNode):
            ast_output.append(f"{indent}Number({ast_node.value})")
        elif isinstance(ast_node, StringNode):
            ast_output.append(f"{indent}String({ast_node.value})")
        elif isinstance(ast_node, IdentifierNode):
            ast_output.append(f"{indent}Identifier({ast_node.value})")
        elif isinstance(ast_node, FunctionCallNode):
            ast_output.append(f"{indent}FunctionCall({ast_node.func_name})")

    # Генерация AST и сохранение в список
    print_ast(node)

    # Сохранение AST в файл
    with open(filename, 'w', encoding='utf-8') as file:
        for line in ast_output:
            file.write(line + '\n')


if __name__ == '__main__':
    main()
