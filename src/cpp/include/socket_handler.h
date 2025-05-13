#ifndef SOCKET_HANDLER_H
#define SOCKET_HANDLER_H

#include <winsock2.h>
#include <ws2tcpip.h>
#include <string>

class SocketHandler {
public:
    SocketHandler();
    ~SocketHandler();
    bool accept_connection();
    std::string read();
    bool write(const std::string& data);

private:
    SOCKET server_socket;
    SOCKET client_socket;
};

#endif