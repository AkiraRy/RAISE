import tkinter
import dotenv
import customtkinter
import os
from PIL import Image
from tkinter import END
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TelegramBot.bot import stop_bot, run_ai, bind
from Modules.errors import ErrorType, handle_error
load_dotenv()
customtkinter.set_default_color_theme(os.getenv('THEME_PATH'))

"""

#TODO
ADD FRAME HANDLING IN MyFrame 
TRYEXCEPT IF DOCKER ENGINE IS NOT RUNNING
MAYBE CHANGE THE ORIGINAL CODE OF WEBUI TO ALSO RETURN TIME THAT PASSED FOR GENERATION
"""

HOST = 'HOST'
WHISPER = 'WHISPER_BASE_URL'
app = None
RESPONSE_TEMPLATE = 'Context %d tokens generated in N seconds'
BOT_STATE = False
gcount=0

def bind_textgen_stats(time_generated, context):
    global gcount, app
    if app is not None:
        print('labe gen')
        label = customtkinter.CTkLabel(app.main_frame.gen_stats_frame, text=f'Context {context} tokens generated in {time_generated} seconds')
        label.grid(row=gcount, column=0)
        gcount+=1
        # CONTINUE FROM HERE


def update_env(key_name: str, value):
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file)
    old_val = os.environ[key_name]  # outputs "value"
    os.environ[key_name] = value
    new_val = os.environ[key_name]  # outputs 'new_value'
    dotenv.set_key(dotenv_file, key_name, os.environ[key_name])
    print(f'Successfully changed {key_name} from {old_val} to {new_val}')


def stop_docker_compose():
    process_check = subprocess.run(['docker-compose', 'ps', '-q'], capture_output=True, text=True)
    if not process_check.stdout.strip():
        print("Docker Compose is not currently running.")
    else:
        process = subprocess.Popen(['docker-compose', 'down'])
        while True:
            time.sleep(1)
            return_code = process.poll()
            if return_code is not None:
                if return_code == 0:
                    print("Docker Compose is stopped.")
                else:
                    print("Failed to stop Docker Compose.")
                break


def start_docker_compose():
    process_check = subprocess.run(['docker-compose', 'ps', '-q'], capture_output=True, text=True)
    if process_check.stdout.strip():
        print("Docker Compose is already running.")
    else:
        process = subprocess.Popen(['docker-compose', 'up', '-d'])
        while True:
            time.sleep(0.1)
            return_code = process.poll()
            if return_code is not None:
                if return_code == 0:
                    print("Docker Compose is up and running.")
                else:
                    print("Failed to start Docker Compose.")
                break


class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, closing, text, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x200")
        self.title(title)

        self.label = customtkinter.CTkLabel(
            self,
            text=text,
            wraplength=300,
            font=customtkinter.CTkFont(family='Aerial', size=15, weight="bold")
        )
        self.label.pack(padx=30, pady=(40, 20))
        if closing is None:
            return

        self.button = customtkinter.CTkButton(self, text='Ok', command=closing)
        self.button.pack(side='bottom', pady=(20, 40), padx=30)
        self.focus()


class MyFrame(customtkinter.CTkFrame):  # Rename to stats main frame probably orstats would be the main page
    def __init__(self, master):
        super().__init__(master)

        self.app = master
        self.current = 'STATS'  # The main idea about different windows, that will appear based on enum
        # configure grid layout (4x4)
        # self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Main system",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )

        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text='Text gen')
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text='Stats', command=master.open_toplevel)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(
            self.sidebar_frame,
            command=master.stop_event,
            text='STOP',
            width=90,
            height=90
        )
        self.sidebar_button_3.grid(row=4, column=0, padx=20, pady=(50, 50))
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_option_menu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_option_menu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_option_menu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event
        )
        self.scaling_option_menu.grid(row=8, column=0, padx=20, pady=(10, 20))

        self.appearance_mode_option_menu.set("Dark")
        self.scaling_option_menu.set("100%")


        self.gen_stats_frame = StatsFrame(self)
        self.gen_stats_frame.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")

        self.buttoin = customtkinter.CTkLabel(self, width=600, text='')
        self.buttoin.grid(row=1, column=1)




    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        self.app.resize(new_scaling_float)
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")


class LoginFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # create login frame
        customtkinter.CTkFrame(master, corner_radius=0)

        self.login_label = customtkinter.CTkLabel(self, text="Starting page",
                                                  font=customtkinter.CTkFont(size=20, weight="bold"))
        self.login_label.grid(row=0, column=0, padx=(30, 30), pady=(150, 15), columnspan=2)

        self.host_entry = customtkinter.CTkEntry(self, width=200, placeholder_text='host')
        self.host_entry.grid(row=1, column=0, padx=(20, 0), pady=(15, 15))

        self.whisper_host = customtkinter.CTkEntry(self, width=200, placeholder_text="whisper host")
        self.whisper_host.grid(row=2, column=0, padx=(20, 0), pady=(0, 15))
        self.launch_button = customtkinter.CTkButton(self, text="Launch", command=master.launch_event, width=230)
        self.launch_button.grid(row=3, column=0, padx=15, columnspan=2, pady=(15, 15))

        self.host_checkbox = customtkinter.CTkCheckBox(
            master=self,
            text='',
            width=1,
            checkbox_height=26,
            checkbox_width=26,
            onvalue=True,
            offvalue=False,
            command=master.host_check
        )
        self.host_checkbox.grid(row=1, column=1, pady=(15, 15), padx=(20, 13))
        self.whisper_checkbox = customtkinter.CTkCheckBox(
            master=self,
            text='',
            width=1,
            checkbox_height=26,
            checkbox_width=26,
            onvalue=True,
            offvalue=False,
            command=master.whisper_check
        )

        self.whisper_checkbox.grid(row=2, column=1, pady=(0, 15), padx=(20, 13))


class StatsFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        # create scrollable frame
        self.width = 500
        # self.uttn = customtkinter.CTkButton(self)
        # self.uttn.grid(row=0, column=0)


class App(customtkinter.CTk):
    width = 1150
    height = 600

    def destroy(self):
        global BOT_STATE
        print(BOT_STATE)
        if BOT_STATE:
            # print('stopping the docker')
            # stop_docker_compose()
            print('stopping the ai')
            stop_bot()
        super().destroy()

    # def close_event(self):
    #     # Stop other threads or perform cleanup operations here
    #     stop_bot()
    #     sys.exit(0)

    def closewd(self):
        self.toplevel_window.destroy()

    def resize(self, scaling):
        new_width = int(self.width*scaling)
        new_height = int(self.height*scaling)
        self.geometry(f'{new_width}x{new_height}')

    def __init__(self):
        super().__init__()
        # self.protocol("WM_DELETE_WINDOW", self.close_event)
        # self.default_host = False
        # self.default_whisper = False
        self.iconbitmap('amadeus.ico')
        self.title('Kurisu control panel')
        self.geometry(f"{self.width}x{self.height}")

        # bg_image
        self.bg_image = customtkinter.CTkImage(
            Image.open(Path(os.getenv('LOGIN_BG'))),
            size=(self.width, self.height)
        )
        self.bg_image_label = customtkinter.CTkLabel(self, text='', image=self.bg_image)
        self.bg_image_label.grid(row=0, column=0)

        # Login Frame
        self.login_frame = LoginFrame(self)
        self.login_frame.grid(row=0, column=0, sticky="ns", columnspan=2)
        self.login_frame.whisper_checkbox.toggle()

        # Main Frame
        self.main_frame = MyFrame(self)

        self.toplevel_window = None

    def stop_event(self):
        global BOT_STATE
        stop_bot()
        self.after(1500, print('\n# ------------- Stopped the bot ----------- #\n'))
        self.main_frame.grid_forget()  # remove main frame
        BOT_STATE = False
        self.login_frame.grid(row=0, column=0, sticky="ns")  # show login frame

    def host_check(self):
        value = self.login_frame.host_checkbox.get()  # True/False
        if value:
            self.login_frame.host_entry.delete(0, END)
            self.login_frame.host_entry.configure(
                placeholder_text='default value for host',
                font=('Roboto', 13, 'italic')
            )
            self.login_frame.host_entry.configure(state=tkinter.DISABLED,)
        else:
            self.login_frame.host_entry.configure(
                state=tkinter.NORMAL,
                placeholder_text='host',
                font=('Roboto', 13, 'normal')
            )
            self.login_frame.host_entry.focus()

    def whisper_check(self):
        value = self.login_frame.whisper_checkbox.get()  # True/False
        if value:
            self.login_frame.whisper_host.delete(0, END)

            self.login_frame.whisper_host.configure(
                placeholder_text='default value for whisper',
                font=('Roboto', 13, 'italic')
            )
            self.login_frame.whisper_host.configure(state=tkinter.DISABLED,)
        else:
            self.login_frame.whisper_host.configure(
                state=tkinter.NORMAL,
                placeholder_text='whisper host',
                font=('Roboto', 13, 'normal')
            )
            self.login_frame.whisper_host.focus()

    def open_toplevel(self, text, title):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(

                text=text,
                title=title,
                closing=self.closewd
            )
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

    def launch_event(self):
        global BOT_STATE

        # Values of entries as well as checkboxes
        whisper_value = self.login_frame.whisper_checkbox.get()
        host_value = self.login_frame.host_checkbox.get()
        host_entry: str = self.login_frame.host_entry.get().strip()
        whisper_entry: str = self.login_frame.whisper_host.get().strip()

        print("Launch pressed\nHost:",
              self.login_frame.host_entry.get(),
              "     Whisper host:",
              self.login_frame.whisper_host.get()
              )

        # Wall of security before giving error values
        if host_value:
            print('default value for host')
        elif not host_value and host_entry == '':
            print('raise warning about host')
            text, title = handle_error(ErrorType.HOST_FAULT, whisper_entry)
            self.open_toplevel(text=text, title=title)
            return
        else:
            update_env(HOST, host_entry)

        if whisper_value:
            print('default value for whisper')
        elif not whisper_value and whisper_entry == '':
            print('raise warning about whisper')  # Create top level window that informs about issue
            text, title = handle_error(ErrorType.WHISPER_FAULT, host_entry)
            self.open_toplevel(text=text, title=title)
            return
        else:
            update_env(WHISPER, whisper_entry.strip())

        self.after(1500)
        print('# ------------- Starting The Docker ------------- #')
        start_docker_compose()

        self.after(1500, print('\n# ------------- Starting the AI ------------- #\n'))
        ai = run_ai()
        ai.set_function(bind_textgen_stats)
        BOT_STATE = True

        self.login_frame.grid_forget()  # remove login frame
        self.main_frame.grid(row=0, column=0, sticky="nsew")  # show main frame
        bind(bind_textgen_stats)


if __name__ == "__main__":
    app = App()
    app.mainloop()
