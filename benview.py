#!/usr/bin/env python

import gi
import sys
from benparser import parse_torrent

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gio

GUI_FILE_PATH = "menu_struct.ui"

class MyWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        Gtk.Window.__init__(self,
                title="Bencoding Viewer", application=app)

        openAction = Gio.SimpleAction.new("open-file", None)
        openAction.connect("activate", self.open_file_callback)
        self.add_action(openAction)

        self.file = None


    def open_file_callback(self, action, parameter):
        openDialog = Gtk.FileChooserDialog(
                title="Pick a bittorrent file",
                parent=self, 
                action=Gtk.FileChooserAction.OPEN, 
                buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        

        # dialog on top of window, always
        openDialog.set_modal(True)

        #connect the callback
        openDialog.connect("response", self.open_response_cb)

        openDialog.show()


    def open_response_cb(self, dialog, responseId):
        openDialog = dialog

        if responseId == Gtk.ResponseType.ACCEPT:
            self.file = openDialog.get_file()
            fileContent =  None

            try:
                [success, content, etags] = self.file.load_contents(None)
                parsed = parse_torrent(content)
                if not parsed:
                    print("Something went wrong...")
                else:
                    print(parsed.poValue)
            except GObject.GError as e:
                print(f"File dialog error: {e.message}")

        dialog.destroy()



class BenviewApplication(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)


    def do_activate(self):
        win = MyWindow(self)
        win.show_all()


    def do_startup(self):
        Gtk.Application.do_startup(self)

        
        quitAction = Gio.SimpleAction.new("quit", None)
        quitAction.connect("activate", self.quit_cb)
        self.add_action(quitAction)


        # set up the app menu
        builder = Gtk.Builder()
        try:
            builder.add_from_file(GUI_FILE_PATH)
        except:
            print(f"Error: Could not build GUI from file {GUI_FILE_PATH}")
            sys.exit()


        menu = builder.get_object("app-menu")
        self.set_app_menu(menu)

    # callbacks
    def quit_cb(self, action, parameter):
        self.quit()




def main():
    app = BenviewApplication()
    exitStatus = app.run(sys.argv)
    sys.exit(exitStatus)

if __name__ == '__main__':
    main()
