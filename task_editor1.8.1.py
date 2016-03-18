#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os

import subprocess

import sqlite3 as sql

import gi
from gi.repository import Gtk, Gdk

DEFAULT_EDITOR = 'gedit'
EDITOR = os.getenv('EDITOR') or DEFAULT_EDITOR

RES_DIR = 'res'
MAIN_PROTO_FILE = os.path.join(RES_DIR, 'iface1.5.3.glade')
FRAME_PROTO_FILE = os.path.join(RES_DIR, 'frame1.3.glade')
STYLES_FILE = os.path.join(RES_DIR, 'style.css')
# ~NODE_NAME = 'offscreenwindow1'
NODE_NAME = 'node_frame1'

NODE_WIDGETS_NAMES_LIST = [
    NODE_NAME,
    'node_textview1',
    'node_del_button1',
    'node_entry2',
    'node_choose_file_button1',
    'node_editor_button1',
    'node_spinbutton1',
    'node_switch1',
    'node_frame_label1',
    'node_adjustment1',
    'node_textbuffer1',
    'node_entrybuffer1',
]

DATA_BLANK = {
    'node_id': -1,
    'note': '',
    'file': '',
    'priority': 0,
    'status': 1,
    'info': ''
}

FILTER_CATEGORIES_MAP = {
    'Sort and search by...': ('node_id', int),
    'Id': ('node_id', int),
    'Note': ('note', str),
    'File': ('file', str),
    'Priority': ('priority', int),
    'State': ('status', bool),
    'Info': ('info', str),
}


class WidgetFactory(object):

    def __init__(self, filename=None, xml=None, filenames=[]):

        if xml:
            self._widget_xml = xml
        elif filename:
            with open(filename) as f:
                self._widget_xml = f.read()

    def get_new_node(self, widget_name=NODE_NAME):

        builder = Gtk.Builder()
        builder.add_from_string(self._widget_xml)

        # ~obj = builder.get_object('frame1')
        # ~obj = builder.get_object(widget_name)
        # ~obj = builder.get_objects()[0]

        obj = {i: builder.get_object(i) for i in NODE_WIDGETS_NAMES_LIST}

        return obj


class App(object):

    def __init__(self, main_proto_file=MAIN_PROTO_FILE, frame_proto_file=FRAME_PROTO_FILE):

        builder = Gtk.Builder()
        builder.add_from_file(main_proto_file)
        builder.connect_signals(self)
        self.window1 = builder.get_object('window1')

        self.window1.connect('destroy', Gtk.main_quit)

        self.builder = builder

        self.entry = builder.get_object('searchentry1')
        self.entrybuf = builder.get_object('entrybuffer1')
        self.entry.connect('search-changed', self.filter_nodes_by)
        
        self.combo = builder.get_object('combobox1')
        self.combo.connect('changed', self.sort_nodes_by)
        # ~self.combo.connect('clicked', self.sort_nodes_by)

        self.listbox = builder.get_object('box5')
        # ~self.listbox = builder.get_object('listbox1')

        self.ffactory = WidgetFactory(filename=frame_proto_file)

        self.cur_filename = ''

        self._reset_nodes_data()
        self._clear_listbox()
        self._init_styles()
        self._init_window_buttons()

        self.window1.show_all()

    def _clear_listbox(self):
        for child in self.listbox.get_children():
            child.destroy()

    def _reset_nodes_data(self):
        self.nodes = {}
        self.nodes_data = {}
        self.fbuttons = {}

    def _init_styles(self):
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(STYLES_FILE)

        self.style_context = Gtk.StyleContext()

        self.style_context.add_provider_for_screen(
            Gdk.Screen.get_default(), 
            self.css_provider,     
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _init_window_buttons(self):
        self.buttons = {}

        self.buttons['add_new_node'] = self.builder.get_object('add_new_node_button')
        self.buttons['add_new_node'].connect('clicked', self.add_node)

    def _setup_node(self, node_id):
        node = self.nodes[node_id]

        data = self.nodes_data[node_id] = {i: DATA_BLANK[i] for i in DATA_BLANK}
        data['node_id'] = node_id

        node['node_textview1'].connect('focus-out-event', self.on_focus_out, node_id)
        node['node_spinbutton1'].connect('focus-out-event', self.on_focus_out, node_id)
        node['node_entry2'].connect('focus-out-event', self.on_focus_out, node_id)
        node['node_switch1'].connect('focus-out-event', self.on_focus_out, node_id)
       
        self._setup_node_buttons(node_id)

    def _setup_node_buttons(self, node_id):
        data = self.nodes_data[node_id]
        node = self.nodes[node_id]

        self.fbuttons[node_id] = dict()

        self.fbuttons[node_id]['choose_file'] = node['node_choose_file_button1']
        self.fbuttons[node_id]['choose_file'].connect('file-set', self.update_frame_name, data['node_id'])

        self.fbuttons[node_id]['del_button1'] = node['node_del_button1']
        self.fbuttons[node_id]['del_button1'].connect('clicked', self.destroy_node, data['node_id'])

        self.fbuttons[node_id]['node_switch1'] = node['node_switch1']
        self.fbuttons[node_id]['node_switch1'].connect('state-set', self.change_node_state, data['node_id'])

        self.fbuttons[node_id]['editor_button1'] = node['node_editor_button1']
        self.fbuttons[node_id]['editor_button1'].connect('clicked', self.open_in_editor, data['node_id'])
        
    def open_in_editor(self, widget, node_id):
        filename = self.nodes_data[node_id]['file']
        if filename:
            node = self.nodes[node_id]
            # ~os.system('{} {}'.format(EDITOR, filename))
            # ~subprocess.call((EDITOR, filename))
            # ~subprocess.check_call((EDITOR, filename))
            lines = node['node_entry2'].get_text().split(' ')
            line = lines[-1]
            if not line.isnumeric():
                line = '0'
            strnum = '+'+str(line)
            subprocess.Popen((EDITOR, strnum, filename))

    def on_exit(self, *args):
        # ~print(args)
        Gtk.main_quit()

    def change_node_state(self, widget=None, state=None, node_id=None):
        data = self.nodes_data[node_id]
        node = self.nodes[node_id]

        # ~state = data['status'] = node['node_switch1'].get_state()
        sc = node['node_frame1'].get_style_context()
        if state==True:
            sc.remove_class('node_frame_inactive')
            sc.add_class('node_frame_active')

        else:
            sc.remove_class('node_frame_active')
            sc.add_class('node_frame_inactive')

    def on_focus_out(self, widget, event, node_id):
        data = self.nodes_data[node_id]
        node = self.nodes[node_id]

        data['note'] = node['node_textbuffer1'].get_text(*node['node_textbuffer1'].get_bounds(), include_hidden_chars=True)
        data['info'] = node['node_entry2'].get_text()
        data['priority'] = node['node_spinbutton1'].get_text()
        # ~data['status'] = node['node_switch1'].get_state()

        # ~print(data)

    def update_nodes_data(self):
        for node_id in self.nodes_data:
            data = self.nodes_data[node_id]
            node = self.nodes[node_id]

            data['note'] = node['node_textbuffer1'].get_text(*node['node_textbuffer1'].get_bounds(), include_hidden_chars=True)
            data['info'] = node['node_entry2'].get_text()
            data['priority'] = node['node_spinbutton1'].get_text()

            label1 = node['node_frame_label1']
            filename = label1.get_text()
            data['file'] = filename

    def update_frame_name(self, widget=None, node_id=None):
        data = self.nodes_data[node_id]
        node = self.nodes[node_id]
        
        label1 = node['node_frame_label1']

        filename = widget.get_filename()
        label1.set_text(filename)
        data['file'] = filename
        
    def destroy_node(self, idget, node_id):
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format='Are you sure want to del task?'
        )

        answer = dialog.run()

        if answer==Gtk.ResponseType.YES:
            node_frame1 = self.nodes[node_id]['node_frame1']
            node_frame1.destroy()

        dialog.destroy()

    def new_file(self, widget=None):
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            type=Gtk.MessageType.WARNING,
            buttons=(
                Gtk.ButtonsType.YES,
                Gtk.ButtonsType.NO,
                Gtk.ButtonsType.CANCEL,
            ),
            message_format='Do you want to save this first?'
        )

        answer = dialog.run()

        if answer==Gtk.ResponseType.YES:
            self.save_file_as()
        elif answer==Gtk.ButtonsType.CANCEL:
            dialog.destroy()
            return

        dialog.destroy()
        self._reset_nodes_data()
        self._clear_listbox()
        self.add_node()

    def save_file(self, *args):
        if self.cur_filename:
            self.update_nodes_data()
            self.dump_nodes(db_filename=self.cur_filename)
        else:
            self.save_file_as()

    def save_file_as(self, *args):
        dialog = Gtk.FileChooserDialog(
            parent=None,
            flags=0,
            action=Gtk.FileChooserAction.SAVE,
            # ~buttons=Gtk.ButtonsType.OK_CANCEL,
            buttons=(
                "Cancel", Gtk.ResponseType.CANCEL,
                "Accept", Gtk.ResponseType.ACCEPT,
            ),
            # ~message_format='Do you want to save this first?'
        )

        ffilter = Gtk.FileFilter()
        ffilter.set_name("*.task")
        ffilter.add_pattern("*.task")
        dialog.add_filter(ffilter)

        answer = (dialog).run()
        if answer == Gtk.ResponseType.ACCEPT:
            self.update_nodes_data()
            filename = dialog.get_filenames()
            # ~print('filename:', filename)
            filename = os.path.abspath(filename[0])
            self.dump_nodes(filename)

        dialog.destroy()

    def open_file(self, *args):
        dialog = Gtk.FileChooserDialog(
            parent=None,
            flags=0,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                "Cancel", Gtk.ResponseType.CANCEL,
                "Accept", Gtk.ResponseType.ACCEPT,
            ),
        )

        ffilter = Gtk.FileFilter()
        ffilter.set_name("Task files")
        ffilter.add_pattern("*.task")
        dialog.add_filter(ffilter)

        answer = (dialog).run()
        if answer == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filenames()
            # ~print('filename:', filename)
            filename = os.path.abspath(filename[0])

            self._reset_nodes_data()
            self._clear_listbox()
            self.load_nodes(filename)
            self.create_nodes()

            self.cur_filename = filename

        dialog.destroy()

    def create_nodes(self):
        for node_id in self.nodes_data:
            # ~node_id = data['node_id']
            data = self.nodes_data[node_id]
            self.add_node(node_id=node_id)

            node = self.nodes[node_id]

            node['node_textbuffer1'].set_text(data['note'])
            node['node_adjustment1'].set_value(data['priority'])
            node['node_frame_label1'].set_text(data['file'])
            node['node_entrybuffer1'].set_text(data['info'], -1)
            node['node_switch1'].set_state(data['status'])

            self.change_node_state(state=data['status'], node_id=data['node_id'])

    def add_node(self, widget=None, node_id=None):
        new_node = self.ffactory.get_new_node()
        node_id = node_id or len(self.nodes)

        self.nodes[node_id] = new_node

        self.listbox.add(self.nodes[node_id][NODE_NAME])
        
        self._setup_node(node_id)

        self.window1.show_all()

    def dump_nodes(self, db_filename):
        conn = sql.connect(db_filename)
        cur = conn.cursor()

        # ~cur.execute("DROP TABLE IF EXISTS tasks")
        cur.execute( \
            """
            CREATE TABLE IF NOT EXISTS tasks(
                node_id INTEGER PRIMARY KEY,
                note TEXT,
                file TEXT,
                priority INTEGER,
                status INTEGER,
                info TEXT
            )        
            """
        )

        # ~print('dumping:', self.nodes_data)
        for node_id in self.nodes_data:
            data = self.nodes_data[node_id]
            # ~print("data:", data)
            cur.execute("INSERT OR REPLACE INTO tasks VALUES ({node_id}, '{note}', '{file}', {priority}, {status}, '{info}')".format(**data))

        conn.commit()
        conn.close()

    def load_nodes(self, db_filename):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d        

        conn = sql.connect(db_filename)
        conn.row_factory = dict_factory
        cur = conn.cursor()

        cur.execute("SELECT * FROM tasks")
        self.nodes_data = {i['node_id']: i for i in cur.fetchall()}

        conn.close()

    def filter_nodes_by(self, *args):

        index = self.combo.get_active()
        model = self.combo.get_model()
        item = model[index]

        category = item[0]
        prop, f = FILTER_CATEGORIES_MAP[category]

        value = self.entry.get_text()

        self.window1.show_all()
        
        if value:
            # ~nodes = filter(lambda x: str(f(value)) in x[prop], self.nodes_data)
            data = self.nodes_data
            # ~print('data.keys:', list(data.keys()))
            # ~print(data[0], prop)
            all_nodes_ids = [data[i]['node_id'] for i in data]
            nodes_ids = [data[i]['node_id'] for i in data if (str(value) in str(data[i][prop]))]
            # ~nodes_ids = [data[i]['node_id'] for i in data if (str(f(value)) in str(data[i][prop]))]
            # ~nodes_data = sorted([data[i] for i in data if str(f(value)) in data[i][prop]], key=lambda x: x[prop])
            # ~nodes_data = sorted([data[i] for i in data if str(f(value)) in data[i][prop]], key=lambda x: x[prop])
            # ~nodes_ids = [i['node_id'] for i in nodes_data]

            to_hide = set(all_nodes_ids) - set(nodes_ids)

            for i in to_hide:
                self.nodes[i]['node_frame1'].hide()

            # ~for i, node_id in enumerate(nodes_ids):
                # ~self.listbox.reorder_child(self.nodes[node_id]['node_frame1'], i)

            # ~print(nodes_ids)
        # ~else:
            # ~for i in all_nodes_ids:
                # ~self.nodes[i]['node_frame1'].hide()

    def sort_nodes_by(self, *args):

        index = self.combo.get_active()
        model = self.combo.get_model()
        item = model[index]

        category = item[0]
        prop, f = FILTER_CATEGORIES_MAP[category]
        
        data = self.nodes_data
        
        nodes_data = sorted([data[i] for i in data], key=lambda x: x[prop])
        nodes_ids = [i['node_id'] for i in nodes_data]

        for i, node_id in enumerate(nodes_ids):
            self.listbox.reorder_child(self.nodes[node_id]['node_frame1'], i)

if __name__ == '__main__':

    window = App()
    window.add_node()
    
    Gtk.main()
