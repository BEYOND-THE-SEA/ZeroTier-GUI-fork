#!/usr/bin/env python3
#
# A Windows front-end for ZeroTier
# Copyright (C) 2023  Tomás Ralph
# Windows adaptation (C) 2023
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##################################
#                                #
#       Created by tralph3       #
#   https://github.com/tralph3   #
#                                #
##################################

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askstring  # added import for askstring
from subprocess import check_output, STDOUT, CalledProcessError
import json
from json import JSONDecodeError
from os import _exit, path, makedirs, environ
from webbrowser import open_new_tab
import sys
from datetime import datetime
import ctypes

# Constants for UI colors and paths
BACKGROUND = "#d9d9d9"  # Default background color
FOREGROUND = "black"  # Default text color
BUTTON_BACKGROUND = "#ffb253"  # Button background color
BUTTON_ACTIVE_BACKGROUND = "#ffbf71"  # Button active background color

# Directory and file for storing network history
HISTORY_FILE_DIRECTORY = path.join(environ["APPDATA"], "zerotier-gui")
HISTORY_FILE_NAME = "network_history.json"

# Paths for ZeroTier configuration on Windows
ZEROTIER_DIR = path.join(environ["ProgramData"], "ZeroTier", "One")
ZEROTIER_AUTH_TOKEN = path.join(ZEROTIER_DIR, "authtoken.secret")


class MainWindow:
    # Configures a Treeview widget with specified columns, widths, and headings
    def _configure_treeview(self, tree, columns, widths, headings):
        tree["show"] = "headings"
        for col, width, heading in zip(columns, widths, headings):
            tree.column(col, width=width)
            tree.heading(col, text=heading)

    # Executes a shell command and returns its output
    def _execute_command(self, command: str) -> str:
        try:
            output = check_output(["cmd", "/c", command], stderr=STDOUT)
            return output.decode()
        except CalledProcessError as e:
            messagebox.showerror("Error", f"Error while executing the command:\n{e.output.decode()}")
            return ""

    # Checks if the current user has administrator privileges
    def _is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    # Retrieves the interface name for a given network index
    def get_interface_name(self, index):
        networks = self.get_networks_info()
        try:
            network_id = networks[index]["id"]
            return f"ZeroTier One [{network_id}]"
        except (IndexError, KeyError):
            return None

    # Verifies if ZeroTier is installed and accessible
    def check_zerotier_installed(self):
        import subprocess
        try:
            output = subprocess.check_output(["zerotier-cli", "-v"], stderr=subprocess.STDOUT)
        except (CalledProcessError, FileNotFoundError):
            messagebox.showerror("Error", "ZeroTier is not installed or not found.\nEnsure that ZeroTier is installed and available in PATH.")
            sys.exit(1)

    # Initializes the main application window and its components
    def __init__(self):
        self.check_zerotier_installed()  # Ensure ZeroTier is installed
        self.load_network_history()  # Load network history from file

        self.window = self.create_window()  # Create the main application window
        self.window.title("ZeroTier-GUI")
        self.window.resizable(width=False, height=False)

        # Layout setup: Define frames for organizing UI components
        self.topFrame = tk.Frame(self.window, padx=20, pady=10, bg=BACKGROUND)
        self.topBottomFrame = tk.Frame(self.window, padx=20, bg=BACKGROUND)
        self.middleFrame = tk.Frame(self.window, padx=20, bg=BACKGROUND)
        self.bottomFrame = tk.Frame(self.window, padx=20, pady=10, bg=BACKGROUND)

        # Define and configure widgets for the UI
        self.networkLabel = tk.Label(
            self.topFrame,
            text="Joined Networks:",
            font=40,
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        self.refreshButton = self.formatted_buttons(
            self.topFrame,
            text="Refresh Networks",
            command=self.refresh_networks,
        )
        self.aboutButton = self.formatted_buttons(
            self.topFrame, text="About", command=self.about_window
        )
        self.peersButton = self.formatted_buttons(
            self.topFrame, text="Show Peers", command=self.see_peers
        )
        self.joinButton = self.formatted_buttons(
            self.topFrame,
            text="Join Network",
            command=self.create_join_network_window,
        )

        # Scrollbar and Treeview for displaying network information
        self.networkListScrollbar = tk.Scrollbar(
            self.middleFrame, bd=2, bg=BACKGROUND
        )
        self.networkList = ttk.Treeview(
            self.middleFrame, columns=("Network ID", "Name", "Status", "State")
        )
        self._configure_treeview(
            self.networkList,
            ["Network ID", "Name", "Status", "State"],
            [100, 150, 100, 100],
            ["Network ID", "Name", "Status", "State"]
        )

        # Bind events to the Treeview for interaction
        self.networkList.bind("<Double-Button-1>", self.call_see_network_info)
        self.networkList.bind("<Button-1>", self.on_network_click)
        self.networkList.bind("<<TreeviewSelect>>", lambda e: self.update_main_buttons())

        # Buttons for network actions
        self.leaveButton = self.formatted_buttons(
            self.bottomFrame,
            text="Leave Network",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=self.leave_network,
        )
        self.ztCentralButton = self.formatted_buttons(
            self.bottomFrame,
            text="ZeroTier Central",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=self.zt_central,
        )
        self.toggleConnectionButton = self.formatted_buttons(
            self.bottomFrame,
            text="Disconnect/Connect Interface (Admin)",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=self.toggle_interface_connection,
        )
        self.infoButton = self.formatted_buttons(
            self.bottomFrame,
            text="Network Info",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=self.see_network_info,
        )
        self.infoButton["state"] = "disabled"  # Initially disabled

        # Pack widgets into their respective frames
        self.networkLabel.pack(side="left", anchor="sw", padx=5)
        self.refreshButton.pack(side="right", anchor="se", padx=5)
        self.aboutButton.pack(side="right", anchor="sw", padx=5)
        self.peersButton.pack(side="right", anchor="sw", padx=5)
        self.joinButton.pack(side="right", anchor="se", padx=5)

        self.networkListScrollbar.pack(side="right", fill="both")
        self.networkList.pack(side="bottom", fill="x")

        self.leaveButton.pack(side="left", fill="x", padx=5)
        self.toggleConnectionButton.pack(side="left", fill="x", padx=5)
        self.infoButton.pack(side="right", fill="x", padx=5)
        self.ztCentralButton.pack(side="right", fill="x", padx=5)

        # Pack frames into the main window
        self.topFrame.pack(side="top", fill="x")
        self.topBottomFrame.pack(side="top", fill="x")
        self.middleFrame.pack(side="top", fill="x")
        self.bottomFrame.pack(side="top", fill="x")

        # Refresh network list and configure scrollbar
        self.refresh_networks()
        self.networkList.config(yscrollcommand=self.networkListScrollbar.set)
        self.networkListScrollbar.config(command=self.networkList.yview)

    # Loads network history from a JSON file
    def load_network_history(self):
        history_file_path = path.join(
            HISTORY_FILE_DIRECTORY, HISTORY_FILE_NAME
        )
        if not path.isfile(history_file_path):
            makedirs(HISTORY_FILE_DIRECTORY, exist_ok=True)
            with open(history_file_path, "w") as f:
                pass
        with open(history_file_path, "r") as f:
            try:
                self.network_history = json.load(f)
            except JSONDecodeError:
                self.network_history = {}

    # Opens the ZeroTier Central website in a browser
    def zt_central(self):
        open_new_tab("https://my.zerotier.com")

    # Calls the network info window when a network is double-clicked
    def call_see_network_info(self, event):
        self.see_network_info()

    # Refreshes the list of paths for a specific peer
    def refresh_paths(self, pathsList, idInList):
        pathsList.delete(*pathsList.get_children())
        pathsData = self.get_peers_info()[idInList]["paths"]
        data = [
            (
              path["active"],
              path["address"],
              path["expired"],
              path["lastReceive"],
              path["lastSend"],
              path["preferred"],
              path["trustedPathId"]
            )
            for path in pathsData
        ]
        for tup in data:
            pathsList.insert("", "end", values=tuple(str(v) for v in tup))

    # Refreshes the list of peers
    def refresh_peers(self, peersList):
        peersList.delete(*peersList.get_children())
        peersData = self.get_peers_info()
        data = [
            (peer["address"], "-" if peer["version"] == "-1.-1.-1" else peer["version"],
             peer["role"], peer["latency"])
            for peer in peersData
        ]
        for peerAddress, peerVersion, peerRole, peerLatency in data:
            peersList.insert("", "end", values=(peerAddress, peerVersion, peerRole, peerLatency))

    # Refreshes the list of networks
    def refresh_networks(self):
        self.networkList.delete(*self.networkList.get_children())
        networkData = self.get_networks_info()
        data = [
            (net["id"],
             net["name"] or "Unknown Name",
             net["status"],
             self.get_interface_state(self.get_interface_name(i))
            )
            for i, net in enumerate(networkData)
        ]
        for networkId, networkName, networkStatus, state in data:
            if not networkName:
                networkName = "Unknown Name"
            if state.lower() == "disabled":
                self.networkList.insert("", "end", values=(networkId, networkName, networkStatus, state),
                                        tags=("down",))
            else:
                self.networkList.insert("", "end", values=(networkId, networkName, networkStatus, state))
        self.networkList.tag_configure("down", background="#ffcccc")
        self.update_network_history_names()

    # Updates network history with names from the current network list
    def update_network_history_names(self):
        networks = self.get_networks_info()
        for network in networks:
            network_id = network["nwid"]
            network_name = network["name"]
            if network_id in self.network_history:
                self.network_history[network_id]["name"] = network_name

    # Saves network history to a JSON file
    def save_network_history(self):
        history_file_path = path.join(
            HISTORY_FILE_DIRECTORY, HISTORY_FILE_NAME
        )
        with open(history_file_path, "w") as f:
            json.dump(self.network_history, f)

    # Retrieves the name of a network by its ID
    def get_network_name_by_id(self, network_id):
        networks = self.get_networks_info()
        for network in networks:
            if network_id == network["nwid"]:
                return network["name"]

    # Retrieves information about all networks
    def get_networks_info(self):
        cmd = "zerotier-cli -j listnetworks"
        data = self._execute_command(cmd)
        return json.loads(data) if data else {}

    # Retrieves information about all peers
    def get_peers_info(self):
        cmd = "zerotier-cli -j peers"
        data = self._execute_command(cmd)
        return json.loads(data) if data else {}

    # Retrieves the status of ZeroTier
    def get_status(self):
        cmd = "zerotier-cli status"
        data = self._execute_command(cmd)
        return data.split() if data else []

    # Launches a sub-window with a specified title
    def launch_sub_window(self, title):
        subWindow = tk.Toplevel(self.window, class_="zerotier-gui")
        subWindow.title(title)
        subWindow.resizable(width=False, height=False)

        return subWindow

    # Creates a selectable text widget
    def selectable_text(
        self, frame, text, justify="left", font="TkDefaultFont"
    ):
        entry = tk.Entry(
            frame,
            relief=tk.FLAT,
            bg=BACKGROUND,
            highlightthickness=0,
            highlightcolor=BACKGROUND,
            fg=FOREGROUND,
            selectforeground=FOREGROUND,
            selectborderwidth=0,
            justify=justify,
            font=font,
            bd=0,
        )
        entry.insert(0, text)
        entry.config(state="readonly", width=len(text))

        return entry

    # Creates a formatted button widget
    def formatted_buttons(
        self,
        frame,
        text="",
        bg=BUTTON_BACKGROUND,
        fg=FOREGROUND,
        justify="left",
        activebackground=BUTTON_ACTIVE_BACKGROUND,
        command="",
        activeforeground=FOREGROUND,
    ):
        button = tk.Button(
            frame,
            text=text,
            bg=bg,
            fg=fg,
            justify=justify,
            activebackground=activebackground,
            activeforeground=activeforeground,
            command=command,
        )
        return button

    # Adds a network to the history
    def add_network_to_history(self, network_id):
        network_name = self.get_network_name_by_id(network_id)
        date = datetime.now()
        join_date = f"{date.year}/{date.month:0>2}/{date.day:0>2} {date.hour:0>2}:{date.minute:0>2}"
        self.network_history[network_id] = {
            "name": network_name,
            "join_date": join_date,
        }

    # Checks if the user is currently on a network
    def is_on_network(self, network_id):
        return any(network["nwid"] == network_id for network in self.get_networks_info())

    # Creates a window for joining a network
    def create_join_network_window(self):
        def join_network(network_id):
            try:
                if self.is_on_network(network_id):
                    join_result = "You're already a member of this network."
                    messagebox.showinfo(
                        icon="info", message=join_result, parent=join_window
                    )
                    return
                check_output(["cmd", "/c", "zerotier-cli", "join", network_id])
                join_result = "Successfully joined network"
                self.add_network_to_history(network_id)
                messagebox.showinfo(
                    icon="info", message=join_result, parent=join_window
                )
                self.refresh_networks()
                join_window.destroy()
            except CalledProcessError:
                join_result = "Invalid network ID"
                messagebox.showinfo(
                    icon="error", message=join_result, parent=join_window
                )

        def populate_network_list():
            network_history_list.delete(*network_history_list.get_children())
            for network_id in self.network_history:
                network_name = self.network_history[network_id]["name"]
                if network_name == "":
                    network_name = "Unknown Name"
                network_history_list.insert("", "end", values=(network_name, network_id))

        def populate_info_sidebar():
            selected_item = network_history_list.focus()
            if selected_item != "":
                item_info = network_history_list.item(selected_item)["values"]
                network_id = item_info[1]
                join_date = self.network_history[network_id]["join_date"]
                network_name = self.network_history[network_id]["name"]
                if network_name == "":
                    network_name = "Unknown Name"
                currently_joined = self.is_on_network(network_id)
            else:
                network_id = "-"
                join_date = "-"
                currently_joined = "-"
                network_name = "-"
            network_id_label.configure(
                text="{:20s}{}".format("Network ID:", network_id)
            )
            network_name_label.configure(
                text="{:20s}{}".format("Name:", network_name)
            )
            last_joined_label.configure(
                text="{:20s}{}".format("Last joined date:", join_date)
            )
            currently_joined_label.configure(
                text="{:20s}{}".format("Currently joined:", currently_joined)
            )

        def on_network_selected(event):
            populate_info_sidebar()
            selected_item = network_history_list.focus()
            item_info = network_history_list.item(selected_item)["values"]
            network_id = item_info[1]
            network_entry_value.set(network_id)

        def delete_history_entry():
            selected_item = network_history_list.focus()
            item_info = network_history_list.item(selected_item).get("values", [])
            if len(item_info) < 2:
                return
            network_id = item_info[1]
            self.network_history.pop(network_id, None)
            populate_network_list()

        join_window = self.launch_sub_window("Join Network")
        join_window.configure(bg=BACKGROUND)

        network_entry_value = tk.StringVar()

        main_frame = tk.Frame(join_window, padx=20, pady=20, bg=BACKGROUND)
        middle_frame = tk.Frame(main_frame, bg=BACKGROUND)
        left_frame = tk.LabelFrame(
            middle_frame, bg=BACKGROUND, fg=FOREGROUND, text="Network History"
        )
        right_frame = tk.LabelFrame(
            middle_frame,
            bg=BACKGROUND,
            fg=FOREGROUND,
            text="Info",
            padx=10,
            pady=10,
            width=300
        )
        right_frame.grid_propagate(False)
        bottom_frame = tk.Frame(main_frame, bg=BACKGROUND)

        join_button = self.formatted_buttons(
            bottom_frame,
            text="Join",
            command=lambda: join_network(network_entry_value.get()),
        )
        delete_history_entry_button = self.formatted_buttons(
            bottom_frame,
            text="Delete history entry",
            command=delete_history_entry,
        )

        join_title = tk.Label(main_frame, text="Join Network", font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
        join_title.grid(row=0, column=0, columnspan=2, pady=(0,10))
        network_history_list = ttk.Treeview(left_frame, columns=("Network",))
        self._configure_treeview(network_history_list, ["Network"], [300], ["Network"])
        network_history_list.configure(height=20, style="NoBackground.Treeview")
        network_history_scrollbar = tk.Scrollbar(
            left_frame, bd=2, bg=BACKGROUND
        )
        network_history_list.config(
            yscrollcommand=network_history_scrollbar.set
        )
        network_history_scrollbar.config(command=network_history_list.yview)

        network_history_list.bind("<<TreeviewSelect>>", on_network_selected)
        network_history_list.bind(
            "<Double-Button-1>", lambda _a: join_button.invoke()
        )

        join_label = tk.Label(
            bottom_frame, text="Network ID:", bg=BACKGROUND, fg=FOREGROUND
        )
        join_entry = tk.Entry(
            bottom_frame,
            width=20,
            font="Monospace",
            textvariable=network_entry_value,
        )

        network_id_label = tk.Label(
            right_frame, font=("Monospace", 11), anchor="w", bg=BACKGROUND, fg=FOREGROUND
        )
        network_name_label = tk.Label(
            right_frame, font=("Monospace", 11), anchor="w", bg=BACKGROUND, fg=FOREGROUND
        )
        last_joined_label = tk.Label(
            right_frame, font=("Monospace", 11), anchor="w", bg=BACKGROUND, fg=FOREGROUND
        )
        currently_joined_label = tk.Label(
            right_frame, font=("Monospace", 11), anchor="w", bg=BACKGROUND, fg=FOREGROUND
        )

        network_id_label.grid(row=0, column=0, sticky="w", padx=2, pady=2)
        network_name_label.grid(row=1, column=0, sticky="w", padx=2, pady=2)
        last_joined_label.grid(row=2, column=0, sticky="w", padx=2, pady=2)
        currently_joined_label.grid(row=3, column=0, sticky="w", padx=2, pady=2)

        populate_network_list()
        populate_info_sidebar()

        network_history_list.pack(side="left", padx=10, pady=10)
        network_history_scrollbar.pack(side="right", fill="y")

        join_label.grid(row=0, column=0, sticky="e", padx=(0,10), pady=2)
        join_entry.grid(row=0, column=1, sticky="w", padx=(0,10), pady=2)
        join_button.grid(row=0, column=2, sticky="w", padx=(0,10), pady=2)
        delete_history_entry_button.grid(row=0, column=3, sticky="w", padx=(0,10), pady=2)

        left_frame.grid(row=2, column=0, sticky="ns", padx=5, pady=10)
        right_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=10)
        middle_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        bottom_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        main_frame.pack(fill="both", expand=True)

    # Leaves a network
    def leave_network(self):
        selected = self.networkList.focus()
        if not selected:
            return
        selectionInfo = self.networkList.item(selected)
        network = selectionInfo["values"][0]
        networkName = selectionInfo["values"][1]
        answer = messagebox.askyesno(
            title="Leave Network",
            message=f"Are you sure you want to "
            f'leave "{networkName}" (ID: {network})?',
        )
        if answer:
            try:
                check_output(["cmd", "/c", "zerotier-cli", "leave", network])
                leaveResult = "Successfully left network"
            except CalledProcessError:
                leaveResult = "Error"
        else:
            return
        messagebox.showinfo(icon="info", message=leaveResult)
        self.refresh_networks()

    # Displays the About window
    def about_window(self):
        statusWindow = self.launch_sub_window("About")
        status = self.get_status()
        
        contentFrame = tk.Frame(statusWindow, bg=BACKGROUND, padx=20, pady=20)
        contentFrame.grid(row=0, column=0, sticky="nsew")
        statusWindow.grid_rowconfigure(0, weight=1)
        statusWindow.grid_columnconfigure(0, weight=1)
        
        titleLabel = tk.Label(contentFrame, text="ZeroTier GUI", font=("TkDefaultFont", 18, "bold"), bg=BACKGROUND, fg=FOREGROUND)
        titleLabel.grid(row=0, column=0, columnspan=2, pady=(0,10))
        
        labels = ["My ZeroTier Address:", "ZeroTier Version:", "ZeroTier GUI Version:", "Status:"]
        values = [status[2], status[3], "1.4.0 (Windows)", status[4]]
        for i, (lab, val) in enumerate(zip(labels, values), start=1):
            l = tk.Label(contentFrame, text=lab, font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            v = tk.Label(contentFrame, text=val, font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            l.grid(row=i, column=0, sticky="e", padx=(0,5), pady=2)
            v.grid(row=i, column=1, sticky="w", pady=2)
        
        closeButton = self.formatted_buttons(contentFrame, text="Close", bg=BUTTON_BACKGROUND, activebackground=BUTTON_ACTIVE_BACKGROUND, command=statusWindow.destroy)
        closeButton.grid(row=i+1, column=0, columnspan=2, pady=(10,0), padx=10)
        
        creditsLabel = tk.Label(contentFrame, text="GUI created by Tomás Ralph", bg=BACKGROUND, fg=FOREGROUND)
        creditsLink = tk.Label(contentFrame, text="github.com/tralph3/zerotier-gui", bg=BACKGROUND, fg="blue", cursor="hand2")
        creditsLink.bind("<Button-1>", lambda e: open_new_tab("https://github.com/tralph3/zerotier-gui"))
        creditsLabel.grid(row=i+2, column=0, columnspan=2, pady=(10,0))
        creditsLink.grid(row=i+3, column=0, columnspan=2)
        
        statusWindow.mainloop()

    # Retrieves the state of a network interface
    def get_interface_state(self, interface):
        # Skip the first two lines (header and separator)
        try:
            output = check_output(["netsh", "interface", "show", "interface"], stderr=STDOUT).decode(errors="replace")
        except CalledProcessError:
            return "UNKNOWN"
        lines = output.splitlines()
        import re
        pattern = re.compile(r"^(?P<admin>\S+)\s+(?P<state>\S+)\s+(?P<type>\S+)\s+(?P<name>.+)$")
        for line in lines[2:]:
            match = pattern.match(line)
            if match:
                name = match.group("name").strip()
                if name == interface:
                    admin_state = match.group("admin").strip().lower()
                    if admin_state.startswith("a") or admin_state.startswith("e"):
                        return "Enabled"
                    elif admin_state.startswith("d"):
                        return "Disabled"
                    else:
                        return admin_state
        return "UNKNOWN"

    # Toggles the connection state of a network interface
    def toggle_interface_connection(self):
        # Get the interface name from the selected network
        selected = self.networkList.focus()
        if not selected:
            messagebox.showinfo("Info", "No network selected")
            return

        index = self.networkList.index(selected)
        interfaceName = self.get_interface_name(index)
        if interfaceName is None:
            interfaceName = askstring("Interface", "Enter the network interface name:")
            if not interfaceName:
                return

        if not self._is_admin():
            answer = messagebox.askyesno("Admin rights required", "Administrative rights are required. Relaunch with elevated privileges?")
            if answer:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)  # SW_HIDE = 0
                sys.exit(0)
            else:
                return

        # Automatically toggle based on the current state without additional confirmation
        state = self.get_interface_state(interfaceName)
        if state.lower() == "disabled":
            command = f'netsh interface set interface name="{interfaceName}" admin=ENABLED'
        else:
            command = f'netsh interface set interface name="{interfaceName}" admin=DISABLED'

        try:
            check_output(command, shell=True, stderr=STDOUT)
            self.refresh_networks()
        except CalledProcessError as e:
            messagebox.showerror("Error", f"Error toggling interface:\n{e.output.decode(errors='replace')}")

    # Displays paths for a specific peer
    def see_peer_paths(self, peerList):
        selected = peerList.focus()
        if not selected:
            return
        info = peerList.item(selected)
        if not info.get("values"):
            return
        peerId = info["values"][0]
        peers_info = self.get_peers_info()
        idx = None
        for i, peer in enumerate(peers_info):
            if peer.get("address") == peerId:
                idx = i
                break
        if idx is None:
            return

        pathsWindow = self.launch_sub_window("Peer Path")
        pathsWindow.configure(bg=BACKGROUND)

        topFrame = tk.Frame(pathsWindow, padx=20, bg=BACKGROUND)
        middleFrame = tk.Frame(pathsWindow, padx=20, bg=BACKGROUND)
        bottomFrame = tk.Frame(pathsWindow, padx=20, pady=10, bg=BACKGROUND)

        peerIdLabel = tk.Label(topFrame, font=40, bg=BACKGROUND, fg=FOREGROUND,
                                text=f'Seeing paths for peer with ID "{str(peerId)}"')
        pathsListScrollbar = tk.Scrollbar(middleFrame, bd=2, bg=BACKGROUND)
        pathsList = ttk.Treeview(middleFrame, columns=("Active", "Address", "Expired", "Last Receive", "Last Send", "Preferred", "Trusted Path ID"))
        self._configure_treeview(
            pathsList,
            ["Active", "Address", "Expired", "Last Receive", "Last Send", "Preferred", "Trusted Path ID"],
            [90, 150, 90, 120, 120, 90, 90],
            ["Active", "Expired", "Address", "Last Receive", "Last Send", "Preferred", "Trusted Path ID"]
        )

        peerIdLabel.pack(side="top", fill="x")
        pathsListScrollbar.pack(side="right", fill="both")
        pathsList.pack(side="bottom", fill="x")

        closeButton = self.formatted_buttons(bottomFrame, text="Close", command=lambda: pathsWindow.destroy())
        refreshButton = self.formatted_buttons(bottomFrame, text="Refresh Paths", command=lambda: self.refresh_paths(pathsList, idx))
        closeButton.pack(side="left", fill="x", padx=10)
        refreshButton.pack(side="right", fill="x", padx=10)

        topFrame.pack(side="top", fill="x", pady=(30, 0))
        middleFrame.pack(side="top", fill="x")
        bottomFrame.pack(side="top", fill="x")

        self.refresh_paths(pathsList, idx)
        pathsList.config(yscrollcommand=pathsListScrollbar.set)
        pathsListScrollbar.config(command=pathsList.yview)

        pathsWindow.mainloop()

    # Displays the peers window
    def see_peers(self):
        def call_see_peer_paths(_event):
            self.see_peer_paths(peersList)

        def update_peers_buttons_state():
            if peersList.selection():
                seePathsButton["state"] = "normal"
            else:
                seePathsButton["state"] = "disabled"

        peersWindow = self.launch_sub_window("Peers")
        peersWindow.configure(bg=BACKGROUND)

        topFrame = tk.Frame(peersWindow, padx=20, bg=BACKGROUND)
        middleFrame = tk.Frame(peersWindow, padx=20, bg=BACKGROUND)
        bottomFrame = tk.Frame(peersWindow, padx=20, pady=10, bg=BACKGROUND)

        peersListScrollbar = tk.Scrollbar(middleFrame, bd=2, bg=BACKGROUND)
        peersList = ttk.Treeview(
            middleFrame, columns=("ZT Address", "Version", "Role", "Latency")
        )
        self._configure_treeview(
            peersList,
            ["ZT Address", "Version", "Role", "Latency"],
            [120, 80, 80, 80],
            ["ZT Address", "Version", "Role", "Latency"]
        )

        peersList.bind("<Double-Button-1>", call_see_peer_paths)
        peersList.bind("<<TreeviewSelect>>", lambda e: update_peers_buttons_state())

        closeButton = self.formatted_buttons(
            bottomFrame,
            text="Close",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=lambda: peersWindow.destroy(),
        )
        refreshButton = self.formatted_buttons(
            bottomFrame,
            text="Refresh Peers",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=lambda: self.refresh_peers(peersList),
        )
        seePathsButton = self.formatted_buttons(
            bottomFrame,
            text="See Paths",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=lambda: self.see_peer_paths(peersList),
        )
        seePathsButton["state"] = "disabled"

        peersListScrollbar.pack(side="right", fill="both")
        peersList.pack(side="bottom", fill="x")

        closeButton.pack(side="left", fill="x", padx=10)
        refreshButton.pack(side="right", fill="x", padx=10)
        seePathsButton.pack(side="right", fill="x", padx=10)

        topFrame.pack(side="top", fill="x", pady=(30, 0))
        middleFrame.pack(side="top", fill="x")
        bottomFrame.pack(side="top", fill="x")
        self.refresh_peers(peersList)

        peersList.config(yscrollcommand=peersListScrollbar.set)
        peersListScrollbar.config(command=peersList.yview)

        peersWindow.mainloop()

    # Displays information about a selected network
    def see_network_info(self):
        selected = self.networkList.focus()
        if not selected:
            return
        selectionInfo = self.networkList.item(selected).get("values", [])
        if not selectionInfo:
            return
        network_id = selectionInfo[0]
        networks = self.get_networks_info()
        currentNetworkInfo = next((net for net in networks if net.get("id") == network_id or net.get("nwid") == network_id), None)
        if currentNetworkInfo is None:
            return

        infoWindow = self.launch_sub_window("Network Info")
        contentFrame = tk.Frame(infoWindow, bg=BACKGROUND, padx=20, pady=20)
        contentFrame.grid(row=0, column=0, sticky="nsew")
        infoWindow.grid_rowconfigure(0, weight=1)
        infoWindow.grid_columnconfigure(0, weight=1)

        titleLabel = tk.Label(contentFrame, text="Network Info", font=("TkDefaultFont", 18, "bold"), bg=BACKGROUND, fg=FOREGROUND)
        titleLabel.grid(row=0, column=0, columnspan=2, pady=(0,10))

        fields = [
            ("Name:", currentNetworkInfo.get("name", "N/A")),
            ("Network ID:", currentNetworkInfo.get("id", "N/A")),
            ("Status:", currentNetworkInfo.get("status", "N/A")),
            ("State:", "UP"),
            ("Type:", currentNetworkInfo.get("type", "N/A")),
            ("Device:", currentNetworkInfo.get("portDeviceName", "N/A")),
            ("Bridge:", currentNetworkInfo.get("bridge", "N/A")),
            ("MAC Address:", currentNetworkInfo.get("mac", "N/A")),
            ("MTU:", currentNetworkInfo.get("mtu", "N/A")),
            ("DHCP:", currentNetworkInfo.get("dhcp", "N/A"))
        ]
        for i, (lab, val) in enumerate(fields, start=1):
            l = tk.Label(contentFrame, text=lab, font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            v = tk.Label(contentFrame, text=val, font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            l.grid(row=i, column=0, sticky="e", padx=(0,5), pady=2)
            v.grid(row=i, column=1, sticky="w", pady=2)

        row = i + 1
        addrs = currentNetworkInfo.get("assignedAddresses")
        if addrs:
            l = tk.Label(contentFrame, text="Assigned Addresses:", font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            l.grid(row=row, column=0, sticky="ne", padx=(0,5), pady=2)
            addrFrame = tk.Frame(contentFrame, bg=BACKGROUND)
            addrFrame.grid(row=row, column=1, sticky="w", pady=2)
            for j, addr in enumerate(addrs):
                addrLabel = tk.Label(addrFrame, text=addr, font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
                addrLabel.grid(row=j, column=0, sticky="w")
            row += 1
        else:
            l = tk.Label(contentFrame, text="Assigned Addresses:", font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            v = tk.Label(contentFrame, text="-", font="Monospace", bg=BACKGROUND, fg=FOREGROUND)
            l.grid(row=row, column=0, sticky="e", padx=(0,5), pady=2)
            v.grid(row=row, column=1, sticky="w", pady=2)
            row += 1

        closeButton = self.formatted_buttons(contentFrame, text="Close", bg=BUTTON_BACKGROUND, activebackground=BUTTON_ACTIVE_BACKGROUND, command=infoWindow.destroy)
        closeButton.grid(row=row, column=0, columnspan=2, pady=(10,0))
        
        infoWindow.mainloop()

    # Creates the main application window
    def create_window(self):
        return tk.Tk(className="zerotier-gui")

    # Handles application exit
    def on_exit(self):
        self.window.destroy()
        sys.exit(0)

    # Handles network list click events
    def on_network_click(self, event):
        item = self.networkList.identify_row(event.y)
        if item == "":
            self.networkList.selection_remove(self.networkList.selection())
        return

    # Updates the state of main buttons based on network selection
    def update_main_buttons(self):
        if self.networkList.selection():
            self.infoButton["state"] = "normal"
            self.toggleConnectionButton["state"] = "normal"   # Enabled when a network is selected
        else:
            self.infoButton["state"] = "disabled"
            self.toggleConnectionButton["state"] = "disabled" # Disabled otherwise


if __name__ == '__main__':
    mainWindow = MainWindow()
    mainWindow.window.protocol("WM_DELETE_WINDOW", mainWindow.on_exit)
    mainWindow.window.mainloop()