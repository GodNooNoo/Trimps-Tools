import subprocess
import shlex
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from threading import Thread
import os
import signal
import time
from datetime import datetime
from humanfriendly import format_timespan


class Optimizer():
    def __init__(self):
        self.kill = False
        self.location = "D:\\Games\\Trimps\\trimps-tools"
        self.results = dict()
        self.results['layout'] = dict()
        self.workers = 4
        self.improvements = 0

    def run_athome(self, preset=None):
        command = f"spire128.exe --athome --boredom {20000 * self.workers} -w {self.workers} -n {'--preset ' + preset if preset else ''}"
        process = subprocess.Popen(
            shlex.split(command), text=True, stdout=subprocess.PIPE, shell=True, cwd=self.location, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        tracker = 0
        while True:
            if self.kill:
                self.kill = False
                self.stop(process)
                self.output()
                self.write_log()
                return

            tracker += 1
            new_line = process.stdout.readline().strip()
            print(new_line)
            if tracker == 1:
                self.improvements += 1
                best = new_line
                ind = best.find("(")
                best = best[ind+1:-2]
                best = best.split(',')
                cycles = best.pop()
                _, value = cycles[1:].split(' ')
                self.results["cycle"] = value
            elif tracker == 2:
                string = new_line
            elif tracker == 3:
                core = new_line
                self.results['layout'][core] = string
                tracker = 0

    def run_layout(self, string):
        command = f"spire128.exe {string} --live --towers -n -w {self.workers}"
        process = subprocess.Popen(
            shlex.split(command), text=True, stdout=subprocess.PIPE, shell=True, cwd=self.location, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        while True:
            if self.kill:
                self.kill = False
                self.stop(process)
            new_line = process.stdout.readline()
            print(new_line)

    def output(self):
        [print(f"Layout {i+1}: \n\t {core} \n\t String:  {string}")
         for i, (core, string) in enumerate(self.results['layout'].items())]

    def write_log(self):
        layouts = len(self.results['layout'].keys())
        time_spent = time.time() - Program.start_time
        colon = "\uA789"
        now = datetime.now()
        time_string = f'{now.year}-{now.month}-{now.day}-{now.hour if now.hour >= 10 else "0" + str(now.hour)}{colon}{now.minute if now.minute >= 10 else "0" + str(now.minute)}'
        sub60 = time_spent < 60
        if sub60:
            average = time_spent / layouts
        else:
            average = time_spent / 60 / layouts
        with open(f"data/results-{time_string}.txt", "w") as f:
            f.write(
                f"{layouts} {'layout' if layouts == 1 else 'layouts'} worked on. Time spent was {format_timespan(time_spent)}. \n")
            f.write(
                f"It took a total of {self.results['cycle']} cycles. Averaging {round(average, 2)} {'seconds' if sub60 else 'minutes'} per layout. \n")
            f.write(
                f"A total of {self.improvements - layouts} improvements were made, averaging {self.improvements / layouts} improvements per layout. \n"
            )
            [f.write(f"Layout {i+1}: \n\t {key} \n\t String:  {value} \n")
             for i, (key, value) in enumerate(self.results['layout'].items())]

    def stop(self, process):
        process.send_signal(signal.CTRL_C_EVENT)
        time.sleep(1)
        process.send_signal(signal.CTRL_C_EVENT)
        time.sleep(1)
        process.send_signal(signal.CTRL_BREAK_EVENT)
        time.sleep(1)


class SwaqHandler():
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("http://swaqvalley.com/td_calc/")
        self.core_mods = ["fireCore", "poisonCore", "lightningCore",
                          "strengthCore", "condenserCore", "rsCore"]

    def enter_values(self):
        for core, string in SpireTD.results['layout'].items():
            self.clear_cores()
            self.paste_keys_id("Save", string)
            core = core.split('/')
            if len(core) > 1:
                for string in core[1:]:
                    mod, value = string.split(':')
                    if mod == "runestones":
                        self.paste_keys_id("rsCore", value, delete=True)
                    else:
                        self.paste_keys_id(f"{mod}Core", value, delete=True)
            el = self.driver.find_element_by_xpath(
                '//*[@id="information"]/div[2]/div[2]/button[3]')
            el.click()
            time.sleep(5)
        input("Done with Swaq? ")
        self.driver.close()

    def paste_keys_id(self, aid, text, delete=False):
        el = self.driver.find_element_by_id(aid)
        if delete:
            el.send_keys(Keys.CONTROL, 'a')
            el.send_keys(Keys.BACKSPACE)
        os.system("echo %s| clip" % text.strip())
        el.send_keys(Keys.CONTROL, 'v')
        if delete:
            el.send_keys(Keys.DELETE)

    def clear_cores(self):
        for mod in self.core_mods:
            self.paste_keys_id(mod, "0", delete=True)


class Main():
    def run(self, choice, preset=None):
        self.start_time = time.time()
        if choice == "L" or choice == "l":
            self.run_layout()
        else:
            self.run_athome(preset)

    def run_athome(self, preset=None):
        optimize_thread = Thread(target=SpireTD.run_athome, args=(preset,))
        optimize_thread.start()
        while not self.check_input():
            pass
        Swaq = SwaqHandler()
        Swaq.enter_values()

    def run_layout(self):
        string = input("Paste a layout string: \n")
        optimize_thread = Thread(target=SpireTD.run_layout, args=(string,))
        optimize_thread.start()
        while not self.check_input():
            pass
        print("Done")

    def check_input(self):
        choice = input("Enter S to stop the current optimization: \n")
        if choice == "S" or choice == "s":
            SpireTD.kill = True
            return True
        return False


if __name__ == "__main__":
    Program = Main()
    SpireTD = Optimizer()
    choice = input(
        "Press enter to run spire@home, type L to work on a specific layout: \n")
    preset = "advanced"
    Program.run(choice, preset)
