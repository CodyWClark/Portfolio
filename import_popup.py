# import_popup.py
# ---------------------------------------------------------------------------------
# Page Definition for Import Popup Window

from datetime import datetime as dt  # noqa: F401

import pandas as pd
import PySimpleGUI as sg

from app.{name} import {name}App

# ------ Variables ------ #
DEFAULT_ICON = "./{name}ICON.ico"
itemsDf = pd.DataFrame()
scheduleDf = pd.DataFrame()
# ------ Parameters ------ #
BORDER_COLOR = "#F7F7F7"
HEADER_COLOR = "#FFFFFF"
HEADER_TEXT_COLOR = "#036346"


# ------ Import Popup Window definition ------ #
def popup_import(context):  # noqa: C901

    layout = [
        [sg.Text("Select files to import", font=("arial", 20, "bold"))],
        [
            sg.Text("Select a file for the items list:"),
            sg.Input(" ", disabled=True, key="fpathItems"),
            sg.Button("Browse", key="importItems"),
        ],
        [
            sg.Text("Select a file for the schedule:"),
            sg.Input(" ", disabled=True, key="fpathSchedule"),
            sg.Button("Browse", key="importSchedule"),
        ],
        [
            sg.Button("Import files", key="importToFrames", pad=((5, 100))),
            sg.Text(" ", key="completion"),
        ],
    ]

    window = sg.Window(
        "Import Files",
        layout,
        margins=(0, 0),
        size=(850, 400),
        resizable=True,
        icon=DEFAULT_ICON,
        background_color=BORDER_COLOR,
        modal=True,
    ).Finalize()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            break

        if event == "importItems":
            window["fpathItems"].update(
                value=sg.popup_get_file(
                    "Select a file for the items list:",
                    no_window=True,
                    file_types=(("CSV Files", "*.csv"),),
                )
            )

        if event == "importSchedule":
            window["fpathSchedule"].update(
                value=sg.popup_get_file(
                    "Select a file for the schedule:",
                    no_window=True,
                    file_types=(("CSV Files", "*.csv"),),
                )
            )

        if event == "importToFrames":
            window["completion"].update(value="Please wait, this may take some time...")
            dfStringItems = str(values["fpathItems"])
            if dfStringItems == " " or not dfStringItems:
                window["completion"].update(
                    value="Error: Please select files for both the items list and schedule."
                )
                continue
            itemsDf = pd.read_csv(f"{dfStringItems}")
            if "Item" not in itemsDf:
                window["completion"].update(
                    value="Error: One or more selected files is invalid."
                )
                continue
            if "Category" not in itemsDf:
                window["completion"].update(
                    value="Error: One or more selected files is invalid."
                )
                continue
            if "PRODUCT_LOC" not in itemsDf:
                itemsDf.insert(itemsDf.columns.size, "PRODUCT_LOC", None)

            itemsDfSmall = itemsDf.drop_duplicates(
                subset=["Item", "Category", "PRODUCT_LOC"], keep="first"
            )
            itemsDfSmall = itemsDfSmall.reset_index(drop=True)
            dfStringSchedule = str(values["fpathSchedule"])
            if dfStringSchedule == " " or not dfStringSchedule:
                window["completion"].update(
                    value="Error: Please select files for both the items list and schedule."
                )
                continue
            scheduleDf = pd.read_csv(f"{dfStringSchedule}")
            scheduleDf["Start Time"] = pd.to_datetime(scheduleDf["Start Time"])
            print(scheduleDf)
            scheduleDf["Start Time"] = scheduleDf["Start Time"].dt.strftime(
                "%m/%d/%Y %#H:%M"
            )
            print(scheduleDf)
            if (
                "Type" not in scheduleDf
                or "First Name" not in scheduleDf
                or "Last Name" not in scheduleDf
            ):
                window["completion"].update(
                    value="Error: One or more selected files is invalid."
                )
                continue
            if "STATION" not in scheduleDf:
                scheduleDf.insert(scheduleDf.columns.size, "STATION", None)
            locationDf = pd.read_csv(
                "app\imports\Square Products.csv",  # noqa: W605
                usecols=[
                    "Item Name",
                    "Category",
                    "Variation Name",
                    "Master List Location",
                ],
            )
            locationDf.drop_duplicates()

            itemsDfSmall["Price Point Name"] = itemsDfSmall["Price Point Name"].fillna(
                ""
            )
            locationDf["Variation Name"] = locationDf["Variation Name"].fillna("")

            for i in range(0, len(itemsDfSmall.index)):
                for j in range(0, len(locationDf.index)):
                    if (
                        itemsDfSmall.at[i, "Item"]
                        + itemsDfSmall.at[i, "Category"]
                        + itemsDfSmall.at[i, "Price Point Name"]
                        == locationDf.at[j, "Item Name"]
                        + locationDf.at[j, "Category"]
                        + locationDf.at[j, "Variation Name"]
                    ):
                        itemsDfSmall.at[i, "PRODUCT_LOC"] = locationDf.at[
                            j, "Master List Location"
                        ]
                        break
            walkIn = 1
            driveThru = "A"
            lastWalkIn = None
            lastDriveThru = None
            for i in range(0, len(scheduleDf.index)):
                if scheduleDf.at[i, "Type"] == "Walk-Up or Bike-In Pick Up":
                    if scheduleDf.at[i, "Start Time"] != lastWalkIn:
                        walkIn = 1
                    else:
                        walkIn += 1
                    if walkIn > 8:
                        scheduleDf.at[i, "STATION"] = "ERROR: Walk-up overflow"
                    elif walkIn > 0:
                        scheduleDf.at[i, "STATION"] = "W" + str(walkIn)
                    lastWalkIn = scheduleDf.at[i, "Start Time"]
                elif scheduleDf.at[i, "Type"] == "Drive-Thru Pick Up":
                    if scheduleDf.at[i, "Start Time"] != lastDriveThru:
                        driveThru = "A"
                    else:
                        driveThruInt = ord(driveThru)
                        driveThruInt += 1
                        driveThru = chr(driveThruInt)
                    if driveThru > "H":
                        scheduleDf.at[i, "STATION"] = "ERROR: Drive-thru overflow"
                    elif driveThru >= "A":
                        scheduleDf.at[i, "STATION"] = "1" + driveThru
                    lastDriveThru = scheduleDf.at[i, "Start Time"]
            colLayout = []
            for i in range(0, len(scheduleDf.index)):
                colLayout += (
                    [
                        sg.Text(
                            "Station for "
                            + str(
                                scheduleDf.at[i, "First Name"]
                                + " "
                                + str(scheduleDf.at[i, "Last Name"])
                                + ", "
                                + str(scheduleDf.at[i, "Start Time"])
                            )
                        ),
                        sg.In(scheduleDf.at[i, "STATION"], key="sched" + str(i)),
                    ],
                )
            colLayout += [[sg.Button("Import", key="importSchedWithStation")]]
            colLayout += [[sg.Text(key="statErr")]]
            layout = [
                [
                    sg.Column(
                        colLayout,
                        scrollable=True,
                        vertical_scroll_only=True,
                        expand_x=True,
                        expand_y=True,
                    )
                ]
            ]
            window1 = sg.Window(
                "Input Station Values",
                layout,
                margins=(0, 0),
                size=(650, 400),
                resizable=True,
                icon=DEFAULT_ICON,
                background_color=BORDER_COLOR,
                modal=True,
            ).Finalize()
            window.close()
            window = window1

        if event == "importSchedWithStation":
            for i in range(0, len(scheduleDf.index)):
                continueFlag = False
                if not values["sched" + str(i)]:
                    window["statErr"].update(
                        value="Error: Please enter a station for all appointments."
                    )
                    break
                toCell = values["sched" + str(i)]
                scheduleDf.at[i, "STATION"] = toCell
                continueFlag = True
            # Items list is next
            if not continueFlag:
                continue
            colLayout = []
            for i in range(0, len(itemsDfSmall.index)):
                colLayout += (
                    [
                        sg.Text(
                            "Product location for "
                            + str(itemsDfSmall.at[i, "Item"])
                            + ", "
                            + str(itemsDfSmall.at[i, "Category"])
                            + " ("
                            + str(itemsDfSmall.at[i, "Price Point Name"])
                            + ")"
                        ),
                        sg.Input(
                            itemsDfSmall.at[i, "PRODUCT_LOC"],
                            background_color=None,
                            key="items" + str(i),
                        ),
                    ],
                )
            colLayout += [[sg.Button("Import", key="importItemsWithLoc")]]
            colLayout += [[sg.Text(key="itemsErr")]]
            layout = [
                [
                    sg.Column(
                        colLayout,
                        scrollable=True,
                        expand_x=True,
                        expand_y=True,
                    )
                ]
            ]
            window2 = sg.Window(
                "Input Product Locations",
                layout,
                margins=(0, 0),
                size=(850, 400),
                resizable=True,
                icon=DEFAULT_ICON,
                background_color=BORDER_COLOR,
                modal=True,
            ).Finalize()
            window.close()
            window = window2

        if event == "importItemsWithLoc":
            for i in range(0, len(itemsDfSmall.index)):
                if not values["items" + str(i)]:
                    window["items" + str(i)].update(
                        background_color="red", text_color="white"
                    )
                else:
                    window["items" + str(i)].update(
                        background_color="#F2EFE8", text_color="#000000"
                    )
            for i in range(0, len(itemsDfSmall.index)):
                continueFlag = False
                if not values["items" + str(i)]:
                    window["itemsErr"].update(
                        value="Error: Please enter a location for all items."
                    )
                    break
                toCell = values["items" + str(i)]
                itemsDfSmall.at[i, "PRODUCT_LOC"] = toCell
                continueFlag = True
            if not continueFlag:
                continue
            for i in range(0, len(itemsDf.index)):
                for j in range(0, len(itemsDfSmall.index)):
                    if itemsDf.at[i, "Item"] == itemsDfSmall.at[j, "Item"]:
                        itemsDf.at[i, "PRODUCT_LOC"] = itemsDfSmall.at[j, "PRODUCT_LOC"]
                        break

            window["itemsErr"].update(value="Complete")
            window.close()
            try:
                {name}App.import_data(scheduleDf)
                {name}App.import_data(itemsDf)
                {name}App.merge_master_list()
                # Refresh tables
                {name}}App.refresh_tables(context)

            except RuntimeWarning:
                sg.popup_quick_message(
                    "Unable to import and merge master list.",
                    icon=DEFAULT_ICON,
                )

    window.close()
