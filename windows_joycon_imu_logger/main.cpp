#include <iostream>
#include <fstream>
#include <iomanip>
#include <thread>
#include <chrono>
#include <map>
#include "JoyShockLibrary.h"
#include "json.hpp"

using json = nlohmann::json;

// Map button bitmask to button names
std::map<int, std::string> buttonNames = {
    {0x01, "DOWN"},
    {0x02, "UP"},
    {0x04, "RIGHT"},
    {0x08, "LEFT"},
    {0x10, "L"},
    {0x20, "ZL"},
    {0x40, "MINUS"},
    {0x80, "CAPTURE"},
    {0x100, "A"},
    {0x200, "B"},
    {0x400, "X"},
    {0x800, "Y"},
    {0x1000, "R"},
    {0x2000, "ZR"},
    {0x4000, "PLUS"},
    {0x8000, "HOME"},
};

void print_orientation(float gx, float gy, float gz) 
{
    std::cout << std::fixed << std::setprecision(3)
              << "Orientation (gyro): X=" << gx
              << " Y=" << gy
              << " Z=" << gz << std::endl;
}

void print_button_events(int prevButtons, int currButtons) 
{
    int changed = prevButtons ^ currButtons;
    int pressed = changed & currButtons;
    for (const auto& [mask, name] : buttonNames) {
        if (pressed & mask) {
            std::cout << "*** Button pressed: " << name << " ***" << std::endl;
            // std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        }
    }
}

int main() {
    int numConnected = JslConnectDevices();
    if (numConnected == 0) {
        std::cout << "No controllers found." << std::endl;
        return 1;
    }

    int handles[16] = {0};
    int numHandles = JslGetConnectedDeviceHandles(handles, 16);
    if (numHandles == 0) {
        std::cout << "No device handles found." << std::endl;
        return 1;
    }

    int deviceId = handles[0];
    int prevButtons = 0;

    std::ofstream logFile("imu_log.json", std::ios::app);
    if (!logFile.is_open()) {
        std::cerr << "Failed to open log file." << std::endl;
        return 1;
    }

    while (1) 
    {
        IMU_STATE imu = JslGetIMUState(deviceId);
        int buttonState = JslGetButtons(deviceId);


        auto now = std::chrono::system_clock::now();
        auto duration = now.time_since_epoch();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
    

        json entry = 
        {
            {"timestamp", {ms}},
            {"accel", {imu.accelX, imu.accelY, imu.accelZ}},
            {"gyro", {imu.gyroX, imu.gyroY, imu.gyroZ}},
            {"buttons", buttonState}
        };

        // Write JSON log line
        logFile << entry.dump() << std::endl;
        logFile.flush();

        // Print orientation
        print_orientation(imu.gyroX, imu.gyroY, imu.gyroZ);

        // Print button press events
        print_button_events(prevButtons, buttonState);
        prevButtons = buttonState;

        // std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    logFile.close();
    JslDisconnectAndDisposeAll();
    return 0;
}
