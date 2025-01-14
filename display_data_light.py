from blessed import Terminal
from read_data import SystemDataCollector as collector

ui = Terminal()
sys = collector()

with ui.fullscreen(), ui.cbreak():
      print(ui.clear)

      print(ui.move_xy(0, 0)+
            ui.bold("PID\tName\tUser\tMemory %"))

      print(ui.move_xy(0, 1) +
            (ui.bold("_"*ui.width)))    

      val = ''
      while val.lower() != 'q':
            val = ui.inkey(timeout=1)
            
            data = sys.get_running_processes()

            for cnt, process in enumerate(data):
                  pid = process["pid"]
                  name = process["name"]
                  username = str(process["username"] or '')
                  memory_percent = process["memory_percent"] *100

                  if cnt >= ui.height-2:
                        break
                  print(ui.move_xy(0, cnt+2) + f"{pid}" +
                        ui.move_right(int((ui.width/4)-int(len(str(pid))))) + f"{name}" +
                        ui.move_right(int((ui.width/4)-int(len(name)))) + f"{username}" +
                        ui.move_right(int((ui.width/4)-int(len(username)))) + "{:.2f}".format(memory_percent))
            #reset ui cursor
            print(ui.move_xy(-ui.width, ui.height))
      
      ui.inkey()
