#include "socket_handler.h"
#include <iostream>
#include <fstream>

#pragma comment(lib, "Ws2_32.lib")

SocketHandler::SocketHandler() : server_socket(INVALID_SOCKET), client_socket(INVALID_SOCKET) {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        throw std::runtime_error("WSAStartup failed: " + std::to_string(WSAGetLastError()));
    }

    server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server_socket == INVALID_SOCKET) {
        WSACleanup();
        throw std::runtime_error("Failed to create socket: " + std::to_string(WSAGetLastError()));
    }

    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
        closesocket(server_socket);
        WSACleanup();
        throw std::runtime_error("Setsockopt failed: " + std::to_string(WSAGetLastError()));
    }

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    server_addr.sin_port = htons(12345);

    if (bind(server_socket, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        closesocket(server_socket);
        WSACleanup();
        throw std::runtime_error("Bind failed: " + std::to_string(WSAGetLastError()));
    }

    if (listen(server_socket, 1) == SOCKET_ERROR) {
        closesocket(server_socket);
        WSACleanup();
        throw std::runtime_error("Listen failed: " + std::to_string(WSAGetLastError()));
    }

    std::ofstream debug("debug.txt", std::ios::app);
    debug << "TCP server initialized on 127.0.0.1:12345\n";
    debug.close();

    std::cout << "TCP server listening on 127.0.0.1:12345" << std::endl;
}

SocketHandler::~SocketHandler() {
    if (client_socket != INVALID_SOCKET) {
        closesocket(client_socket);
    }
    if (server_socket != INVALID_SOCKET) {
        closesocket(server_socket);
    }
    WSACleanup();
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Closed TCP sockets\n";
    debug.close();
    std::cout << "Closed TCP sockets" << std::endl;
}

bool SocketHandler::accept_connection() {
    std::cout << "Waiting for client connection..." << std::endl;
    client_socket = accept(server_socket, NULL, NULL);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Accept failed: " << WSAGetLastError() << std::endl;
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Accept failed: " << WSAGetLastError() << "\n";
        debug.close();
        return false;
    }
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Client connected\n";
    debug.close();
    std::cout << "Client connected" << std::endl;
    return true;
}

std::string SocketHandler::read() {
    char buffer[1024 * 1024];
    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (bytes_received == SOCKET_ERROR) {
        int error = WSAGetLastError();
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Read failed: " << error << "\n";
        debug.close();
        if (error == WSAECONNRESET || error == WSAECONNABORTED) {
            std::cout << "Client disconnected, error: " << error << ". Waiting for new connection..." << std::endl;
            closesocket(client_socket);
            client_socket = INVALID_SOCKET;
            return "";
        }
        std::cerr << "Read failed: " << error << std::endl;
        return "";
    }
    if (bytes_received == 0) {
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Client closed connection\n";
        debug.close();
        std::cout << "Client closed connection. Waiting for new connection..." << std::endl;
        closesocket(client_socket);
        client_socket = INVALID_SOCKET;
        return "";
    }
    buffer[bytes_received] = '\0';
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Received: " << std::string(buffer).substr(0, 50) << "...\n";
    debug.close();
    std::cout << "Received: " << std::string(buffer).substr(0, 50) << "..." << std::endl;
    return std::string(buffer);
}

bool SocketHandler::write(const std::string& data) {
    int bytes_sent = send(client_socket, data.c_str(), data.size(), 0);
    if (bytes_sent == SOCKET_ERROR) {
        int error = WSAGetLastError();
        std::ofstream debug("debug.txt", std::ios::app);
        debug << "Write failed: " << error << "\n";
        debug.close();
        if (error == WSAECONNRESET || error == WSAECONNABORTED) {
            std::cout << "Client disconnected during write, error: " << error << ". Waiting for new connection..." << std::endl;
            closesocket(client_socket);
            client_socket = INVALID_SOCKET;
            return false;
        }
        std::cerr << "Write failed: " << error << std::endl;
        return false;
    }
    std::ofstream debug("debug.txt", std::ios::app);
    debug << "Sent: " << data.substr(0, 50) << "...\n";
    debug.close();
    std::cout << "Sent: " << data.substr(0, 50) << "..." << std::endl;
    return true;
}