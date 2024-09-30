import socket

LOCALHOST = "0.0.0.0"
BUFFER_SIZE = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
    connection.connect((LOCALHOST, 10001))
    a, b = map(
        int, 
        connection
            .recv(BUFFER_SIZE)
            .decode()
            .strip()
            .split("*")
    )
    connection.send(b"HelloWorld," + str(a * b).encode())

    response = connection.recv(BUFFER_SIZE).decode().strip()
    print(response)