import threading
import time
import fliclib
from samplebase import SampleBase
from rgbmatrix import graphics


c = threading.Condition()
client = fliclib.FlicClient("localhost")
player1 = "80:e4:da:72:59:b6"
player2 = "80:e4:da:72:90:ae"
player1Score = 0
player2Score = 0
serverDirection = "<"

def click_handler(channel, click_type, was_queued, time_diff):
    global player1Score
    global player2Score
    global serverDirection

    print(str(channel.bd_addr))

    c.acquire()

    if str(click_type) == "ClickType.ButtonSingleClick":
        if str(channel.bd_addr) == player1:
            player1Score += 1
        elif str(channel.bd_addr) == player2:
            player2Score += 1

        player1Score = player1Score
        player2Score = player2Score

    if str(click_type) == "ClickType.ButtonDoubleClick":
        if str(channel.bd_addr) == player1:
            if player1Score > 0:
                player1Score -= 1
        elif str(channel.bd_addr) == player2:
            if player2Score > 0:
                player2Score -= 1
        
        click_type = str(click_type)
        player1Score = player1Score
        player2Score = player2Score

    if str(click_type) == "ClickType.ButtonHold":
        if str(channel.bd_addr) == player1:
            player1Score = 0
        elif str(channel.bd_addr) == player2:
            player2Score = 0
        
        click_type = str(click_type)
        player1Score = player1Score
        player2Score = player2Score

    total = (player1Score + player2Score)

    if total % 5 == 0 and total > 0:
        if serverDirection == ">":
            serverDirection = "<"
        else:
            serverDirection = ">"
    elif total == 0:
        serverDirection = "<"

    c.notify_all()
    c.wait()


def got_button(bd_addr):
    cc = fliclib.ButtonConnectionChannel(bd_addr)
    cc.on_button_single_or_double_click_or_hold = click_handler
    cc.on_connection_status_changed = \
        lambda channel, connection_status, disconnect_reason: \
            print(channel.bd_addr + " " + str(connection_status) + (" " + str(disconnect_reason) if connection_status == fliclib.ConnectionStatus.Disconnected else ""))
    client.add_connection_channel(cc)

def got_info(items):
    print(items)
    for bd_addr in items["bd_addr_of_verified_buttons"]:
        got_button(bd_addr)

class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)

    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("/home/pi/pong/fonts/clR6x12.bdf")
        textFont = graphics.Font()
        textFont.LoadFont("/home/pi/pong/fonts/4x6.bdf")
        textColor = graphics.Color(255, 255, 0)
        redText = graphics.Color(255, 38, 0)

        largeNumberOffest = 4

        pos1_x = 15
        pos1_x_offset = pos1_x - largeNumberOffest
        pos2_x = 44
        pos2_x_offset = pos2_x - largeNumberOffest

        pos1_y = 24
        pos2_y = pos1_y

        graphics.DrawText(offscreen_canvas, font, pos1_x, pos1_y, textColor, str(player1Score))
        graphics.DrawText(offscreen_canvas, font, pos2_x, pos2_y, textColor, str(player2Score))

        while True:
            offscreen_canvas.Clear()

            # Outer Circle
            for x in range(0, offscreen_canvas.width):
                offscreen_canvas.SetPixel(x, 0, 19, 49, 186)
                offscreen_canvas.SetPixel(x, offscreen_canvas.height - 1, 19, 49, 186)

            for y in range(0, offscreen_canvas.height):
                offscreen_canvas.SetPixel(0, y, 19, 49, 186)
                offscreen_canvas.SetPixel(offscreen_canvas.width - 1, y, 19, 49, 186)

            # Inner Circle
            for x in range(3, offscreen_canvas.width - 3):
                offscreen_canvas.SetPixel(x, 2, 19, 49, 186)
                offscreen_canvas.SetPixel(x, offscreen_canvas.height - 3, 19, 49, 186)

            for y in range(3, offscreen_canvas.height - 3):
                offscreen_canvas.SetPixel(3, y, 19, 49, 186)
                offscreen_canvas.SetPixel(offscreen_canvas.width - 4, y, 19, 49, 186)

            c.acquire()

            if player1Score <= 9:
                graphics.DrawText(offscreen_canvas, font, pos1_x, pos1_y, textColor, str(player1Score))
            else:
                graphics.DrawText(offscreen_canvas, font, pos1_x_offset, pos1_y, textColor, str(player1Score))

            if player2Score <= 9:
                graphics.DrawText(offscreen_canvas, font, pos2_x, pos2_y, textColor, str(player2Score))
            else:
                graphics.DrawText(offscreen_canvas, font, pos2_x_offset, pos2_y, textColor, str(player2Score))


            graphics.DrawText(offscreen_canvas, textFont, 14, 13, textColor, "P1")
            graphics.DrawText(offscreen_canvas, textFont, offscreen_canvas.width - 21, 13, textColor, "P2")

            # Server Arrow
            graphics.DrawText(offscreen_canvas, textFont, 30, 22, redText, serverDirection)

            c.notify_all()
            c.release()

            time.sleep(0.05)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)


class Thread_A(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name


    def run(self):
        run_text = RunText()
        if (not run_text.process()):
            run_text.print_help()

class Thread_B(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global client
        client.get_info(got_info)
        client.on_new_verified_button = got_button
        event = client.handle_events()


a = Thread_A("pixel_thread")
b = Thread_B("flic_thread")

b.start()
a.start()

a.join()
b.join()


def signal_handler(signal, frame):
  sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
