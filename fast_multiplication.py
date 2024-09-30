import time
import re
import random
import threading
import socket
from datetime import datetime
from typing import Iterable

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"

BRACKET_COLOUR = MAGENTA
TIME_COLOUR = BLUE

HOST = '0.0.0.0'
PORT = 10001

NUMBER_MAX = 100
NUMBER_MIN = 50
ANSWER_REGEX = re.compile(r"^[A-Za-z- ]+, ?\d+$")
GUESS_TIME = 1.0

succesful_students = []
lock = threading.Lock()

def andjoin(sep: str, s: Iterable[str]) -> str:
    if not s:
        return ""
    
    *rest, last = s
    if len(s) == 1:
        return str(last)
    return str(sep.join(rest) + " and " + last)

def fancy_print(colour: str, s: str):
    now = datetime.now()
    now_without_millis = str(now).rsplit('.', 1)[0]
    now_replaced = now_without_millis.replace("-", "/")
    print(
        f"{BRACKET_COLOUR}[{TIME_COLOUR}{now_replaced}{BRACKET_COLOUR}]: "
        f"{colour}{s}{RESET}"
    )

def handle_client(connection: socket.socket):
    with connection:
        num1 = random.randint(NUMBER_MIN, NUMBER_MAX)
        num2 = random.randint(NUMBER_MIN, NUMBER_MAX)
        numbers = f"{num1} * {num2}\n"
        
        connection.sendall(numbers.encode())
        start_time = time.time()
        try:
            if not (data := connection.recv(1024)):
                return
        except ConnectionResetError:
            return
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        response = data.decode().strip()
        if not ANSWER_REGEX.search(response):
            connection.sendall(
                b"Your answer must be in the format "
                b"'name, answer', matching the regex "
                + ANSWER_REGEX.pattern.encode() + b'\n'
            )
            return

        student_name, response_number = response.split(',', 1)
        response_number = response_number.strip()
        student_name = student_name.strip()
        
        correct_product = num1 * num2
        try:
            client_product = int(response_number)
        except (ValueError, TypeError):
            answer_is_correct = False
        else:
            answer_is_correct = client_product == correct_product
        within_time = elapsed_time < GUESS_TIME
        
        if answer_is_correct and within_time:
            reply = "Correct! Well done.\n"
            if student_name in succesful_students:
                reply = "You have already completed the task."
            else:
                if not succesful_students:
                    fancy_print(GREEN, 
                        f"{student_name} is the first to "
                        "complete the challenge! Well done!"
                    )
                with lock:
                    succesful_students.append(student_name)
                fancy_print(GREEN, 
                    f"{student_name} successfully completed the task."
                )
                fancy_print(MAGENTA,
                    "Succesful students: " + andjoin(", ", succesful_students)
                )
        elif not answer_is_correct and within_time:
            reply = "Incorrect product.\n"
            fancy_print(RED, 
                f"{student_name} guessed {response_number}"
                f"but the correct answer was {correct_product}."
            )
        elif answer_is_correct and not within_time:
            reply = "Correct, but you took too long :(.\n"
            fancy_print(YELLOW, 
                f"{student_name} guessed correctly but took too long :("
            )
        else:
            reply = "Incorrect product and too slow.\n"
            fancy_print(CYAN, 
                f"{student_name} took too long to answer."
            )
        
        connection.sendall(reply.encode())

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    fancy_print(YELLOW, "Starting")
    fancy_print(CYAN, f"Server is listening on {HOST}:{PORT}")
    
    with server_socket:
        while True:
            connection = server_socket.accept()[0]
            client_thread = threading.Thread(target=handle_client, args=(connection,))
            client_thread.daemon = True
            client_thread.start()

if __name__ == "__main__":
    start_server()