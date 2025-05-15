# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++14 -Wall -I./src/cpp/include -lws2_32
LDFLAGS = -static

# Source directory
SRC_DIR = ./src/cpp/src

# Executable directory and name
BIN_DIR = ./bin
TARGET = $(BIN_DIR)/virtual_memory_simulator.exe

# Find all cpp files
SRCS = $(wildcard $(SRC_DIR)/*.cpp)

# Create bin dir if missing
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Build executable by compiling all cpp files directly
$(TARGET): $(BIN_DIR)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS)

# Clean executable
.PHONY: clean
clean:
	rm -rf $(TARGET)
