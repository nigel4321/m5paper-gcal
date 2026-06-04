import M5
M5.begin()
M5.Lcd.setRotation(0)
M5.Lcd.fillScreen(0xFFFFFF)
M5.Lcd.setFont(M5.Lcd.FONTS.Montserrat40)
M5.Lcd.setTextSize(1)
M5.Lcd.setTextColor(0x000000, 0xFFFFFF)
# Same drawString, called at six y-positions
for y in (40, 200, 400, 600, 800, 900):
    M5.Lcd.drawString("Test {}".format(y), 24, y)