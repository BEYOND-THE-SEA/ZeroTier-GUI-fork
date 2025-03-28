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
from subprocess import check_output, STDOUT, CalledProcessError
import json
from json import JSONDecodeError
from os import _exit, path, makedirs, environ
from webbrowser import open_new_tab
import sys
from datetime import datetime
import textwrap
import ctypes

# Chemins adaptés pour Windows
BACKGROUND = "#d9d9d9"
FOREGROUND = "black"
BUTTON_BACKGROUND = "#ffb253"
BUTTON_ACTIVE_BACKGROUND = "#ffbf71"

# Définition du répertoire pour l'historique sur Windows
HISTORY_FILE_DIRECTORY = path.join(environ["APPDATA"], "zerotier-gui")
HISTORY_FILE_NAME = "network_history.json"

# Chemins pour ZeroTier sur Windows
ZEROTIER_DIR = path.join(environ["ProgramData"], "ZeroTier", "One")
ZEROTIER_AUTH_TOKEN = path.join(ZEROTIER_DIR, "authtoken.secret")


class MainWindow:
    def __init__(self):
        self.load_network_history()

        self.window = self.create_window()  # Assurez-vous de créer la fenêtre principale

        self.window.title("ZeroTier-GUI")
        self.window.resizable(width=False, height=False)

        # layout setup
        self.topFrame = tk.Frame(self.window, padx=20, pady=10, bg=BACKGROUND)
        self.topBottomFrame = tk.Frame(self.window, padx=20, bg=BACKGROUND)
        self.middleFrame = tk.Frame(self.window, padx=20, bg=BACKGROUND)
        self.bottomFrame = tk.Frame(
            self.window, padx=20, pady=10, bg=BACKGROUND
        )

        # widgets
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

        self.networkListScrollbar = tk.Scrollbar(
            self.middleFrame, bd=2, bg=BACKGROUND
        )

        self.networkList = ttk.Treeview(
            self.middleFrame, columns=("Network ID", "Name", "Status")
        )
        self.networkList["show"] = "headings"
        self.networkList.column("Network ID", width=100)
        self.networkList.column("Name", width=150)
        self.networkList.column("Status", width=100)
        # Ajout des en-têtes pour les colonnes
        self.networkList.heading("Network ID", text="Network ID")
        self.networkList.heading("Name", text="Name")
        self.networkList.heading("Status", text="Status")

        self.networkList.bind("<Double-Button-1>", self.call_see_network_info)

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
        
        # Boutons désactivés pour Windows
        self.toggleConnectionButton = self.formatted_buttons(
            self.bottomFrame,
            text="Disconnect/Connect Interface (Disabled on Windows)",
            bg=BACKGROUND,
            activebackground=BACKGROUND,
            command=lambda: messagebox.showinfo("Info", "Cette fonction n'est pas disponible sur Windows"),
        )
        
        self.infoButton = self.formatted_buttons(
            self.bottomFrame,
            text="Network Info",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=self.see_network_info,
        )

        # pack widgets
        self.networkLabel.pack(side="left", anchor="sw")
        self.refreshButton.pack(side="right", anchor="se")
        self.aboutButton.pack(side="right", anchor="sw")
        self.peersButton.pack(side="right", anchor="sw")
        self.joinButton.pack(side="right", anchor="se")

        self.networkListScrollbar.pack(side="right", fill="both")
        self.networkList.pack(side="bottom", fill="x")

        self.leaveButton.pack(side="left", fill="x")
        self.toggleConnectionButton.pack(side="left", fill="x")
        self.infoButton.pack(side="right", fill="x")
        self.ztCentralButton.pack(side="right", fill="x")

        # frames
        self.topFrame.pack(side="top", fill="x")
        self.topBottomFrame.pack(side="top", fill="x")
        self.middleFrame.pack(side="top", fill="x")
        self.bottomFrame.pack(side="top", fill="x")

        # extra configuration
        self.refresh_networks()

        self.networkList.config(yscrollcommand=self.networkListScrollbar.set)
        self.networkListScrollbar.config(command=self.networkList.yview)

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

    # Méthodes liées aux services Linux supprimées ou désactivées
    # toggle_service, get_service_status, update_service_label

    def zt_central(self):
        open_new_tab("https://my.zerotier.com")

    def call_see_network_info(self, event):
        self.see_network_info()

    def refresh_paths(self, pathsList, idInList):
        pathsList.delete(*pathsList.get_children())
        paths = []
        # outputs info of paths in json format
        pathsData = self.get_peers_info()[idInList]["paths"]

        # get paths information in a list of tuples
        for pathPosition in range(len(pathsData)):
            paths.append(
                (
                    pathsData[pathPosition]["active"],
                    pathsData[pathPosition]["address"],
                    pathsData[pathPosition]["expired"],
                    pathsData[pathPosition]["lastReceive"],
                    pathsData[pathPosition]["lastSend"],
                    pathsData[pathPosition]["preferred"],
                    pathsData[pathPosition]["trustedPathId"],
                )
            )

        # set paths in listbox
        for (
            pathActive,
            pathAddress,
            pathExpired,
            pathLastReceive,
            pathLastSend,
            pathPreferred,
            pathTrustedId,
        ) in paths:
            pathsList.insert(
                "",
                "end",
                values=(
                    str(pathActive),
                    str(pathAddress),
                    str(pathExpired),
                    str(pathLastReceive),
                    str(pathLastSend),
                    str(pathPreferred),
                    str(pathTrustedId),
                )
            )

    def refresh_peers(self, peersList):
        peersList.delete(*peersList.get_children())
        peers = []
        # outputs info of peers in json format
        peersData = self.get_peers_info()

        # get peers information in a list of tuples
        for peerPosition in range(len(peersData)):
            peers.append(
                (
                    peersData[peerPosition]["address"],
                    peersData[peerPosition]["version"],
                    peersData[peerPosition]["role"],
                    peersData[peerPosition]["latency"],
                )
            )

        # set peers in listbox
        for peerAddress, peerVersion, peerRole, peerLatency in peers:
            if peerVersion == "-1.-1.-1":
                peerVersion = "-"
            peersList.insert("", "end", values=(peerAddress, peerVersion, peerRole, peerLatency))

    def refresh_networks(self):
        self.networkList.delete(*self.networkList.get_children())
        networks = []
        # outputs info of networks in json format
        networkData = self.get_networks_info()

        # gets networks information in a list of tuples
        for networkPosition in range(len(networkData)):
            networks.append(
                (
                    networkData[networkPosition]["id"],
                    networkData[networkPosition]["name"],
                    networkData[networkPosition]["status"],
                    False,  # isDown - non applicable sur Windows, on le met à False
                )
            )
        # set networks in listbox
        for (
            networkId,
            networkName,
            networkStatus,
            isDown,
        ) in networks:
            if not networkName:
                networkName = "Unknown Name"
            self.networkList.insert(
                "", "end", values=(networkId, networkName, networkStatus)
            )

        self.update_network_history_names()

    def update_network_history_names(self):
        networks = self.get_networks_info()
        for network in networks:
            network_id = network["nwid"]
            network_name = network["name"]
            if network_id in self.network_history:
                self.network_history[network_id]["name"] = network_name

    def save_network_history(self):
        history_file_path = path.join(
            HISTORY_FILE_DIRECTORY, HISTORY_FILE_NAME
        )
        with open(history_file_path, "w") as f:
            json.dump(self.network_history, f)

    def get_network_name_by_id(self, network_id):
        networks = self.get_networks_info()
        for network in networks:
            if network_id == network["nwid"]:
                return network["name"]

    def get_networks_info(self):
        # La commande à exécuter
        command = "zerotier-cli -j listnetworks"
        try:
            # On utilise cmd /c afin de lancer le .bat présent dans le PATH
            output = check_output(["cmd", "/c", command], stderr=STDOUT)
            # print(output.decode())
            return json.loads(output.decode())
        except CalledProcessError as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution de la commande:\n{e.output.decode()}")
            return {}

    def get_peers_info(self):
        # La commande à exécuter
        command = "zerotier-cli -j peers"
        try:
            # On utilise cmd /c afin de lancer le .bat présent dans le PATH
            output = check_output(["cmd", "/c", command], stderr=STDOUT)
            return json.loads(output.decode())
        except CalledProcessError as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution de la commande:\n{e.output.decode()}")
            return {}

    def get_status(self):
        # La commande à exécuter
        command = "zerotier-cli status"
        try:
            # On utilise cmd /c afin de lancer le .bat présent dans le PATH
            output = check_output(["cmd", "/c", command], stderr=STDOUT)
            return output.decode().split()
        except CalledProcessError as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution de la commande:\n{e.output.decode()}")
            return []

    def launch_sub_window(self, title):
        subWindow = tk.Toplevel(self.window, class_="zerotier-gui")
        subWindow.title(title)
        subWindow.resizable(width=False, height=False)

        return subWindow

    # creates entry widgets to select and copy text
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

    # creates correctly formatted buttons
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

    def add_network_to_history(self, network_id):
        network_name = self.get_network_name_by_id(network_id)
        date = datetime.now()
        join_date = f"{date.year}/{date.month:0>2}/{date.day:0>2} {date.hour:0>2}:{date.minute:0>2}"
        self.network_history[network_id] = {
            "name": network_name,
            "join_date": join_date,
        }

    def is_on_network(self, network_id):
        currently_joined = False
        for network in self.get_networks_info():
            if currently_joined:
                break
            currently_joined = network["nwid"] == network_id
        return currently_joined

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
            item_info = network_history_list.item(selected_item)["values"]
            network_id = item_info[1]
            self.network_history.pop(network_id)
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
        )
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

        join_title = tk.Label(
            main_frame, text="Join Network", font="Monospace"
        )
        network_history_list = ttk.Treeview(left_frame, columns=("Network",))
        network_history_scrollbar = tk.Scrollbar(
            left_frame, bd=2, bg=BACKGROUND
        )
        network_history_list.config(
            yscrollcommand=network_history_scrollbar.set
        )
        network_history_scrollbar.config(command=network_history_list.yview)

        network_history_list.style = ttk.Style()
        network_history_list.style.configure(
            "NoBackground.Treeview", background=BACKGROUND
        )
        network_history_list.configure(
            show="tree", height=20, style="NoBackground.Treeview"
        )
        network_history_list.column("Network", width=300)
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
            right_frame, font=("Monospace", 11), width=45, anchor="w"
        )
        network_name_label = tk.Label(
            right_frame, font=("Monospace", 11), width=45, anchor="w"
        )
        last_joined_label = tk.Label(
            right_frame,
            font=("Monospace", 11),
            width=45,
            anchor="w",
        )
        currently_joined_label = tk.Label(
            right_frame,
            font=("Monospace", 11),
            width=45,
            anchor="w",
        )

        populate_network_list()
        populate_info_sidebar()

        join_title.pack(side="top")
        network_history_list.pack(side="left", padx=10, pady=10)
        network_history_scrollbar.pack(side="right", fill="y")

        network_id_label.pack(side="top", anchor="w")
        network_name_label.pack(side="top", anchor="w")
        last_joined_label.pack(side="top", anchor="w")
        currently_joined_label.pack(side="top", anchor="w")

        join_label.pack(side="left", anchor="w", pady=10)
        join_entry.pack(side="left", anchor="w", pady=10)
        join_button.pack(side="left", pady=10)
        delete_history_entry_button.pack(side="left", pady=10)

        left_frame.pack(side="left", fill="y", pady=10, padx=5)
        right_frame.pack(side="right", fill="y", pady=10, padx=5)
        middle_frame.pack(side="top", fill="both")
        bottom_frame.pack(side="top", fill="both")
        main_frame.pack(side="top", fill="x")

    def leave_network(self):
        # get selected network
        try:
            selectionId = int(self.networkList.focus())
            selectionInfo = self.networkList.item(selectionId)
        except TypeError:
            messagebox.showinfo(
                icon="info", title="Error", message="No network selected"
            )
            return
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

    def about_window(self):
        statusWindow = self.launch_sub_window("About")
        status = self.get_status()

        # frames
        topFrame = tk.Frame(statusWindow, padx=20, pady=30, bg=BACKGROUND)
        middleFrame = tk.Frame(statusWindow, padx=20, pady=10, bg=BACKGROUND)
        bottomTopFrame = tk.Frame(
            statusWindow, padx=20, pady=10, bg=BACKGROUND
        )
        bottomFrame = tk.Frame(statusWindow, padx=20, pady=10, bg=BACKGROUND)

        # widgets
        titleLabel = tk.Label(
            topFrame,
            text="ZeroTier GUI",
            font=70,
            bg=BACKGROUND,
            fg=FOREGROUND,
        )

        ztAddrLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("My ZeroTier Address:", status[2]),
        )
        versionLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("ZeroTier Version:", status[3]),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        ztGuiVersionLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("ZeroTier GUI Version:", "1.4.0 (Windows)"),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        statusLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Status:", status[4]),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )

        closeButton = self.formatted_buttons(
            bottomTopFrame,
            text="Close",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=lambda: statusWindow.destroy(),
        )

        # credits
        creditsLabel1 = tk.Label(
            bottomFrame,
            text="GUI created by Tomás Ralph",
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        creditsLabel2 = self.selectable_text(
            bottomFrame,
            text="github.com/tralph3/zerotier-gui",
            justify="center",
        )

        # pack widgets
        titleLabel.pack(side="top", anchor="n")

        ztAddrLabel.pack(side="top", anchor="w")
        versionLabel.pack(side="top", anchor="w")
        ztGuiVersionLabel.pack(side="top", anchor="w")
        statusLabel.pack(side="top", anchor="w")

        closeButton.pack(side="top")

        creditsLabel1.pack(side="top", fill="x")
        creditsLabel2.pack(side="top")

        topFrame.pack(side="top", fill="both")
        middleFrame.pack(side="top", fill="both")
        bottomTopFrame.pack(side="top", fill="both")
        bottomFrame.pack(side="top", fill="both")

        statusWindow.mainloop()

    # Méthode désactivée pour Windows
    def get_interface_state(self, interface):
        # Sur Windows, nous ne pouvons pas facilement obtenir l'état de l'interface comme sur Linux
        # Nous retournons "UP" par défaut
        return "UP"

    # Méthode désactivée pour Windows
    def toggle_interface_connection(self):
        messagebox.showinfo(
            icon="info", 
            title="Non disponible", 
            message="La fonction de connexion/déconnexion d'interface n'est pas disponible sur Windows"
        )

    def see_peer_paths(self, peerList):
        selected = peerList.focus()
        if not selected:
            return
        info = peerList.item(selected)
        if not info.get("values"):
            return
        peerId = info["values"][0]
        # Find index of peer in the peers info list by matching address
        peers_info = self.get_peers_info()
        idx = None
        for i, peer in enumerate(peers_info):
            if peer.get("address") == peerId:
                idx = i
                break
        if idx is None:
            return

        # Create a new window for displaying peer paths
        pathsWindow = self.launch_sub_window("Peer Path")
        pathsWindow.configure(bg=BACKGROUND)

        # Create frames
        topFrame = tk.Frame(pathsWindow, padx=20, bg=BACKGROUND)
        middleFrame = tk.Frame(pathsWindow, padx=20, bg=BACKGROUND)
        bottomFrame = tk.Frame(pathsWindow, padx=20, pady=10, bg=BACKGROUND)

        # Create widgets for paths display
        peerIdLabel = tk.Label(topFrame, font=40, bg=BACKGROUND, fg=FOREGROUND,
                                text=f'Seeing paths for peer with ID "{str(peerId)}"')
        pathsListScrollbar = tk.Scrollbar(middleFrame, bd=2, bg=BACKGROUND)
        pathsList = ttk.Treeview(middleFrame, columns=("Active", "Address", "Expired", "Last Receive", "Last Send", "Preferred", "Trusted Path ID"))
        pathsList["show"] = "headings"
        pathsList.column("Active", width=90)
        pathsList.column("Address", width=150)
        pathsList.column("Expired", width=90)
        pathsList.column("Last Receive", width=120)
        pathsList.column("Last Send", width=120)
        pathsList.column("Preferred", width=90)
        pathsList.column("Trusted Path ID", width=90)
        pathsList.heading("Active", text="Active")
        pathsList.heading("Expired", text="Expired")
        pathsList.heading("Address", text="Address")
        pathsList.heading("Last Receive", text="Last Receive")
        pathsList.heading("Last Send", text="Last Send")
        pathsList.heading("Preferred", text="Preferred")
        pathsList.heading("Trusted Path ID", text="Trusted Path ID")

        # Pack widgets
        peerIdLabel.pack(side="top", fill="x")
        pathsListScrollbar.pack(side="right", fill="both")
        pathsList.pack(side="bottom", fill="x")

        closeButton = self.formatted_buttons(bottomFrame, text="Close", command=lambda: pathsWindow.destroy())
        refreshButton = self.formatted_buttons(bottomFrame, text="Refresh Paths", command=lambda: self.refresh_paths(pathsList, idx))
        closeButton.pack(side="left", fill="x")
        refreshButton.pack(side="right", fill="x")

        topFrame.pack(side="top", fill="x", pady=(30, 0))
        middleFrame.pack(side="top", fill="x")
        bottomFrame.pack(side="top", fill="x")

        self.refresh_paths(pathsList, idx)
        pathsList.config(yscrollcommand=pathsListScrollbar.set)
        pathsListScrollbar.config(command=pathsList.yview)

        pathsWindow.mainloop()

    def see_peers(self):
        def call_see_peer_paths(_event):
            self.see_peer_paths(peersList)

        peersWindow = self.launch_sub_window("Peers")
        peersWindow.configure(bg=BACKGROUND)

        # frames
        topFrame = tk.Frame(peersWindow, padx=20, bg=BACKGROUND)
        middleFrame = tk.Frame(peersWindow, padx=20, bg=BACKGROUND)
        bottomFrame = tk.Frame(peersWindow, padx=20, pady=10, bg=BACKGROUND)

        # widgets
        peersListScrollbar = tk.Scrollbar(middleFrame, bd=2, bg=BACKGROUND)
        peersList = ttk.Treeview(
            middleFrame, columns=("ZT Address", "Version", "Role", "Latency")
        )
        peersList["show"] = "headings"
        peersList.column("ZT Address", width=120)
        peersList.column("Version", width=80)
        peersList.column("Role", width=80)
        peersList.column("Latency", width=80)
        peersList.heading("ZT Address", text="ZT Address")
        peersList.heading("Version", text="Version")
        peersList.heading("Role", text="Role")
        peersList.heading("Latency", text="Latency")
        peersList.bind("<Double-Button-1>", call_see_peer_paths)

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

        # pack widgets
        peersListScrollbar.pack(side="right", fill="both")
        peersList.pack(side="bottom", fill="x")

        closeButton.pack(side="left", fill="x")
        refreshButton.pack(side="right", fill="x")
        seePathsButton.pack(side="right", fill="x")

        topFrame.pack(side="top", fill="x", pady=(30, 0))
        middleFrame.pack(side="top", fill="x")
        bottomFrame.pack(side="top", fill="x")
        self.refresh_peers(peersList)

        peersList.config(yscrollcommand=peersListScrollbar.set)
        peersListScrollbar.config(command=peersList.yview)

        peersWindow.mainloop()

    def see_network_info(self):
        selected = self.networkList.focus()
        if not selected:
            return
        selectionInfo = self.networkList.item(selected).get("values", [])
        if not selectionInfo:
            return
        network_id = selectionInfo[0]  # Use first column (Network ID)
        networks = self.get_networks_info()
        currentNetworkInfo = None
        for net in networks:
            if net.get("id") == network_id or net.get("nwid") == network_id:
                currentNetworkInfo = net
                break
        if currentNetworkInfo is None:
            return

        infoWindow = self.launch_sub_window("Network Info")

        # frames
        topFrame = tk.Frame(infoWindow, pady=30, bg=BACKGROUND)
        middleFrame = tk.Frame(infoWindow, padx=20, bg=BACKGROUND)
        bottomFrame = tk.Frame(infoWindow, pady=10, bg=BACKGROUND)

        # Génération des widgets pour les adresses assignées
        try:
            assignedAddressesWidgets = []
            # Premier widget
            assignedAddressesWidgets.append(
                self.selectable_text(
                    middleFrame,
                    "{:25s}{}".format(
                        "Assigned Addresses:", currentNetworkInfo["assignedAddresses"][0]
                    ),
                    font="Monospace",
                )
            )
            # Widgets suivants s'il y a plusieurs adresses
            for address in currentNetworkInfo["assignedAddresses"][1:]:
                assignedAddressesWidgets.append(
                    self.selectable_text(
                        middleFrame,
                        "{:>42s}".format(address),
                        font="Monospace",
                    )
                )
        except (IndexError, KeyError):
            assignedAddressesWidgets = []
            assignedAddressesWidgets.append(
                self.selectable_text(
                    middleFrame,
                    "{:25s}{}".format("Assigned Addresses:", "-"),
                    font="Monospace",
                )
            )

        # Création des widgets d'affichage
        titleLabel = tk.Label(
            topFrame,
            text="Network Info",
            font=70,
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        nameLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Name:", currentNetworkInfo.get("name", "N/A")),
        )
        idLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Network ID:", currentNetworkInfo.get("id", "N/A")),
        )
        statusLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Status:", currentNetworkInfo.get("status", "N/A")),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        # Sur Windows, nous renvoyons "UP" par défaut pour l'état de l'interface
        stateLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("State:", "UP"),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        typeLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Type:", currentNetworkInfo.get("type", "N/A")),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        deviceLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Device:", currentNetworkInfo.get("portDeviceName", "N/A")),
        )
        bridgeLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("Bridge:", currentNetworkInfo.get("bridge", "N/A")),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )
        macLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("MAC Address:", currentNetworkInfo.get("mac", "N/A")),
        )
        mtuLabel = self.selectable_text(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("MTU:", currentNetworkInfo.get("mtu", "N/A")),
        )
        dhcpLabel = tk.Label(
            middleFrame,
            font="Monospace",
            text="{:25s}{}".format("DHCP:", currentNetworkInfo.get("dhcp", "N/A")),
            bg=BACKGROUND,
            fg=FOREGROUND,
        )

        closeButton = self.formatted_buttons(
            bottomFrame,
            text="Close",
            bg=BUTTON_BACKGROUND,
            activebackground=BUTTON_ACTIVE_BACKGROUND,
            command=lambda: infoWindow.destroy(),
        )

        # Pack des widgets
        titleLabel.pack(side="top", anchor="n")
        nameLabel.pack(side="top", anchor="w")
        idLabel.pack(side="top", anchor="w")
        for widget in assignedAddressesWidgets:
            widget.pack(side="top", anchor="w")
        statusLabel.pack(side="top", anchor="w")
        stateLabel.pack(side="top", anchor="w")
        typeLabel.pack(side="top", anchor="w")
        deviceLabel.pack(side="top", anchor="w")
        bridgeLabel.pack(side="top", anchor="w")
        macLabel.pack(side="top", anchor="w")
        mtuLabel.pack(side="top", anchor="w")
        dhcpLabel.pack(side="top", anchor="w")
        closeButton.pack(side="top")

        # Pack des frames
        topFrame.pack(side="top", fill="both")
        middleFrame.pack(side="top", fill="both")
        bottomFrame.pack(side="top", fill="both")

        infoWindow.mainloop()

    def create_window(self):
        return tk.Tk(className="zerotier-gui")

    def on_exit(self):
        self.window.destroy()
        sys.exit(0)


if __name__ == '__main__':
    mainWindow = MainWindow()
    mainWindow.window.protocol("WM_DELETE_WINDOW", mainWindow.on_exit)
    mainWindow.window.mainloop()