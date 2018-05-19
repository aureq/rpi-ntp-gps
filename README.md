# warning
This repository is merely usable as it's just a brain dump of my own work. Use at your own risk.

# hardware
 - Raspberry 2 (Could worrk on Raspberry 1 and Raspberry 3)
 - RTC DS3231
   - LiR 2032 or CR2032
 - Ublox neo 6M
   - GPS antena and SMA patch cable
 - TFT Screen 480x320 3.5" for Raspberry 1 (Adafruit)
 - Ethernet cable (Wi-Fi should be fine too)
 - 5v - 2.5A power supply

# hardware setup
 - RTC DS3231
   - Insert the battery into the RTC module
   - Remove the diode if using a non-rechargeable battery from the RTC module
   - Connect the RTC to the I2C bus (`SDA` and `SCL`)
   - Connect `SQW`  to GPIO 22
   - Connect `VCC` pin to `3.3v` and `GND` pin to `GND`

 - Ublox Neo 6M
   - Connect `TX` to `UART0_RXD`
   - Connect `RX` to `UART0_TXD`
   - Connect `PPS` to GPIO 4
   - Connect `VCC` pin to `3.3v` and `GND` pin to `GND`

 - TFT Screen 480x320 3.5"
   - Install screen on top of rPi header
