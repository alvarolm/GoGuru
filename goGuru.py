# Copyright (c) 2014 Jesse Meek <https://github.com/waigani>
# Copyright (c) 2016 Alvaro Leiva <https://github.com/alvarolm>
# This program is Free Software see LICENSE file for details.

"""
GoGuru is a Go guru plugin for Sublime Text 3.
It depends on the guru tool being installed:
go get golang.org/x/tools/cmd/guru
"""

import sublime, sublime_plugin, subprocess, time, re, os, subprocess, sys

DEBUG = False
VERSION = ''
PluginPath = ''
use_golangconfig = False


def log(*msg):
    print("GoGuru:", msg[0:])

def debug(*msg):
    if DEBUG:
        print("GoGuru [DEBUG]:", msg[0:])

def error(*msg):
        print("GoGuru [ERROR]:", msg[0:])

def plugin_loaded():
    global DEBUG
    global VERSION
    global PluginPath
    global use_golangconfig

    DEBUG = get_setting("debug", False)
    PluginPath = sublime.packages_path()+'/GoGuru/'
    use_golangconfig = get_setting("use_golangconfig", False)

    # load shellenv
    def load_shellenv():
        sys.path.append(PluginPath+"/dep/")
        global shellenv
        import shellenv

    # try golangconfig
    if use_golangconfig:
        try:
            global golangconfig
            import golangconfig    
        except:
            error("couldn't import golangconfig:", sys.exc_info()[0])
            log("using shellenv instead of golangconfig")
            use_golangconfig = False
            load_shellenv()
        
    else:
        load_shellenv()



    log("debug:", DEBUG)
    log("use_golangconfig", use_golangconfig)

    # keep track of the version if possible
    try:
        p = subprocess.Popen(["git", "describe", "master", "--tags"], stdout=subprocess.PIPE, cwd=PluginPath)
        GITVERSION = p.communicate()[0].decode("utf-8").rstrip()
        if p.returncode != 0:
             debug("git return code", p.returncode)
        f = open(PluginPath+'VERSION', 'w')
        f.write(GITVERSION)
        f.close()
    except:
        debug("couldn't get git tag:", sys.exc_info()[0])

    # read version
    f = open(PluginPath+'VERSION', 'r')
    VERSION = f.read().rstrip()
    f.close()
    log("version:", VERSION)


class GoGuruCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view 
        self.mode = 'None'
    def run(self, edit, mode=None):

        region = self.view.sel()[0]
        text = self.view.substr(sublime.Region(0, region.end()))
        cb_map = self.get_map(text)
        byte_end = cb_map[sorted(cb_map.keys())[-1]]
        byte_begin = None
        if not region.empty(): 
            byte_begin = cb_map[region.begin()-1]

        if mode:
            self.write_running(mode)
            self.guru(byte_end, begin_offset=byte_begin, mode=mode, callback=self.guru_complete)
            return

        # Get the guru mode from the user.
        modes = ["callees","callers","callstack","definition","describe","freevars","implements","peers","pointsto","referrers","what","callgraph"]
        descriptions  = [
            "callees     show possible targets of selected function call",
            "callers     show possible callers of selected function",
            "callstack   show path from callgraph root to selected function",
            "definition  show declaration of selected identifier",
            "describe    describe selected syntax: definition, methods, etc",
            "freevars    show free variables of selection",
            "implements  show 'implements' relation for selected type or method",
            "peers       show send/receive corresponding to selected channel op",
            "pointsto    show variables the selected pointer may point to",
            "referrers   show all refs to entity denoted by selected identifier",
            "what        show basic information about the selected syntax node",
            "callgraph   show complete callgraph of program"]

        # Call guru cmd with the given mode.
        def on_done(i):
            if i >= 0 :
                self.write_running(modes[i])

                self.guru(byte_end, begin_offset=byte_begin, mode=modes[i], callback=self.guru_complete)

        self.view.window().show_quick_panel(descriptions, on_done, sublime.MONOSPACE_FONT)

    def guru_complete(self, out, err):
        self.write_out(out, err)

    def write_running(self, mode):
        """ Write the "Running..." header to a new file and focus it to get results
        """
        # remember mode for future actions
        self.mode = mode

        window = self.view.window()
        view = get_output_view(window)

        # Run a new command to use the edit object for this view.
        view.run_command('go_guru_write_running', {'mode': mode})

        if get_setting("output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

    def write_out(self, result, err):
        """ Write the guru output to a new file.
        """

        window = self.view.window()
        view = get_output_view(window)

        # Run a new command to use the edit object for this view.
        view.run_command('go_guru_write_results', {
            'result': result,
            'err': err})

        if get_setting("output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

        # jump to definition if is set
        if self.mode == 'definition':
            if get_setting("jumpto_definition", False):
                if result:
                    coordinates = result.split(':')[:3]
                    new_view = window.open_file(':'.join(coordinates), sublime.ENCODED_POSITION)
                    group, _ = window.get_view_index(new_view)
                    if group != -1:
                        window.focus_group(group)

    def get_map(self, chars):
        """ Generate a map of character offset to byte offset for the given string 'chars'.
        """

        byte_offset = 0
        cb_map = {}

        for char_offset, char in enumerate(chars):
            cb_map[char_offset] = byte_offset
            byte_offset += len(char.encode('utf-8'))
        return cb_map

    def guru(self, end_offset, begin_offset=None, mode="describe", callback=None):
        """ Builds the guru shell command and calls it, returning it's output as a string.
        """

        pos = "#" + str(end_offset)
        if begin_offset is not None:
            pos = "#%i,#%i" %(begin_offset, end_offset)

        file_path = self.view.file_name()

        # golang config or shellenv ?
        cmd_env = ''
        if use_golangconfig:
            try:
                toolpath, cmd_env = golangconfig.subprocess_info('guru', ['GOPATH', 'PATH'], view=self.view)
                toolpath = os.path.realpath(toolpath)
            except:
                error("golangconfig:", sys.exc_info())
                return
        else:
            toolpath = 'guru'
            cmd_env = shellenv.get_env(for_subprocess=True)[1]
            cmd_env.update(get_setting("env", {}))

        debug("env", cmd_env)

        guru_scope = ",".join(get_setting("guru_scope", ""))

        # add local package to guru scope
        if get_setting("use_current_package", True) :
            current_file_path = os.path.realpath(os.path.dirname(file_path))
            GOPATH = os.path.realpath(cmd_env["GOPATH"]+"/src")+"/"
            local_package = current_file_path.replace(GOPATH, "")
            debug("current_file_path", current_file_path)
            debug("GOPATH", GOPATH)
            debug("local_package", local_package)
            guru_scope = guru_scope+','+local_package
        guru_scope = guru_scope.strip()
        debug("guru_scope", guru_scope)
        if len(guru_scope) > 0:
            guru_scope = "-scope "+guru_scope

        guru_json = ""
        if get_setting("guru_json", False):
            guru_json = "-json"

        # Build guru cmd.
        cmd = "%(toolpath)s %(scope)s %(guru_json)s %(mode)s %(file_path)s:%(pos)s" % {
        "toolpath": toolpath,
        "file_path": file_path,
        "pos": pos,
        "guru_json": guru_json,
        "mode": mode,
        "scope": guru_scope} 
        debug("cmd", cmd)

        sublime.set_timeout_async(lambda: self.runInThread(cmd, callback, cmd_env), 0)

    def runInThread(self, cmd, callback, env):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, env=env)
        out, err = proc.communicate()
        callback(out.decode('utf-8'), err.decode('utf-8'))


class GoGuruWriteResultsCommand(sublime_plugin.TextCommand):
    """ Writes the guru output to the current view.
    """

    def run(self, edit, result, err):
        view = self.view

        view.insert(edit, view.size(), "\n")

        if result:
            view.insert(edit, view.size(), result)
        if err:
            view.insert(edit, view.size(), err)

        view.insert(edit, view.size(), "\n\n\n")
        

class GoGuruWriteRunningCommand(sublime_plugin.TextCommand):
    """ Writes the guru output to the current view.
    """

    def run(self, edit, mode):
        view = self.view

        content = "Running guru " + mode + " command...\n"
        view.set_viewport_position(view.text_to_layout(view.size() - 1))

        view.insert(edit, view.size(), content)


class GoGuruShowResultsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if get_setting("output", "buffer") == "output_panel":
            self.view.window().run_command('show_panel', {'panel': "output.Oracle Output" })
        else:
            output_view = get_output_view(self.view.window())
            self.view.window().focus_view(output_view)


class GoGuruOpenResultCommand(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
      if view.name() == "Oracle Output":
        if len(view.sel()) != 1:
            return
        if view.sel()[0].size() == 0:
            return

        lines = view.lines(view.sel()[0])
        if len(lines) != 1:
            return

        line = view.full_line(lines[0])
        text = view.substr(line)

        format = get_setting("guru_format")

        # "filename:line:col" pattern for json
        m = re.search("\"([^\"]+):([0-9]+):([0-9]+)\"", text)

        # >filename:line:col< pattern for xml
        if m == None:
            m = re.search(">([^<]+):([0-9]+):([0-9]+)<", text)

        # filename:line.col-line.col: pattern for plain
        if m == None:
            m = re.search("^([^:]+):([0-9]+).([0-9]+)[-: ]", text)
        
        if m:
            w = view.window()
            new_view = w.open_file(m.group(1) + ':' + m.group(2) + ':' + m.group(3), sublime.ENCODED_POSITION)
            group, index = w.get_view_index(new_view)
            if group != -1:
                w.focus_group(group)


def get_output_view(window):
    view = None
    buff_name = 'Oracle Output'

    if get_setting("output", "buffer") == "output_panel":
        view = window.create_output_panel(buff_name)
    else:
        # If the output file is already open, use that.
        for v in window.views():
            if v.name() == buff_name:
                view = v
                break
        # Otherwise, create a new one.
        if view is None:
            view = window.new_file()

    view.set_name(buff_name)
    view.set_scratch(True)
    view_settings = view.settings()
    view_settings.set('line_numbers', False)
    view.set_syntax_file('Packages/GoGuru/GoGuruResults.tmLanguage')

    return view

def get_setting(key, default=None):
    """ Returns the setting in the following hierarchy: project setting, user setting, 
    default setting.  If none are set the 'default' value passed in is returned.
    """

    val = None
    try:
       val = sublime.active_window().active_view().settings().get('GoGuru', {}).get(key)
    except AttributeError:
        pass

    if not val:
        val = sublime.load_settings("User.sublime-settings").get(key)
    if not val:
        val = sublime.load_settings("Default.sublime-settings").get(key)
    if not val:
        val = default
    return val