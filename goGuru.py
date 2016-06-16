# Copyright (c) 2014 Jesse Meek <https://github.com/waigani>
# Copyright (c) 2016 Alvaro Leiva <https://github.com/alvarolm>
# This program is Free Software see LICENSE file for details.

"""
GoGuru is a Go guru plugin for Sublime Text 3.
It depends on the guru tool being installed:
go get golang.org/x/tools/cmd/guru
"""

# TODO: review & clean

import sublime, sublime_plugin, subprocess, time, re, os, subprocess, sys

def log(*msg):
    print("GoGuru:", msg[0:])

def debug(*msg):
    if get_setting("goguru_debug", False):
        print("GoGuru [DEBUG]:", msg[0:])

def error(*msg):
        print("GoGuru [ERROR]:", msg[0:])

def plugin_loaded():
    # load shellenv
    def load_shellenv():
        global shellenv
        from .dep import shellenv

    # try golangconfig
    if get_setting("goguru_use_golangconfig", False):
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

    log("debug:", get_setting("goguru_debug", False))
    log("use_golangconfig", get_setting("goguru_use_golangconfig", False))

    # keep track of the version if possible (pretty nasty workaround, any other ideas ?)
    try:
        PluginPath = os.path.dirname(os.path.realpath(__file__))
        p = subprocess.Popen(["git", "describe", "master", "--tags"], stdout=subprocess.PIPE, cwd=PluginPath)
        GITVERSION = p.communicate()[0].decode("utf-8").rstrip()
        if p.returncode != 0:
             debug("git return code", p.returncode)
             raise Exception("git return code", p.returncode) 


        defsettings = os.path.join(PluginPath, 'Default.sublime-settings')
        f = open(defsettings,'r')
        filedata = f.read()
        f.close()
        newdata = filedata.replace(get_setting('goguru_version'), GITVERSION+'_')
        f = open(defsettings,'w')
        f.write(newdata)
        f.close()
    except:
        debug("couldn't get git tag:", sys.exc_info()[0])

    # read version
    log("version:", get_setting('goguru_version'))

    # check if user setting exists and creates it
    us = sublime.load_settings("GoGuru.sublime-settings")
    if (not us.has('goguru_debug')):
        us.set('goguru_debug', get_setting("goguru_debug", False))
        sublime.save_settings("GoGuru.sublime-settings")

class GoGuruCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view 
        self.mode = 'None'
        self.env = 'None'
        self.local_package = 'None'
    def run(self, edit, mode=None):

        try:
            region = self.view.sel()[0]
            text = self.view.substr(sublime.Region(0, region.end()))
            cb_map = self.get_map(text)
            byte_end = cb_map[sorted(cb_map.keys())[-1]]
            byte_begin = None
            if not region.empty(): 
                byte_begin = cb_map[region.begin()-1]
        except:
            sublime.error_message('GoGuru:\nCouldn\'t get cursor positon, make sure that the Go source file is saved and the cursor is over the identifier (variable, function ...) you want to query.')
            error("couldn't get cursor positon: ", sys.exc_info())
            return

        if mode:
            self.write_running(mode)
            # expiremental
            # uses gosublime gs_doc commands to look for documentation
            # if it fails pareses the 'guru describe' output to query 'go doc'
            if mode == "godoc":
                self.view.window().run_command('gs_doc', {'mode': "hint"})
                gsdoc = self.view.window().find_output_panel('GsDoc-output-output')
                if gsdoc != None:
                    if not 'no docs found' in gsdoc.substr(gsdoc.line(0)):
                        return
                def messageLookingDoc():
                    self.write_out(None, "'gs_doc' failed,\nsearching documentation with 'goguru godoc'...")
                sublime.set_timeout(lambda: messageLookingDoc(), 110) # any other choice besides timeout ? 
                mode = "describe"
                self.guru(byte_end, begin_offset=byte_begin, mode=mode, callback=self.guru_complete)
            return

        # Get the guru mode from the user.
        modes = ["callees","callers","callstack","definition","describe","freevars","implements","peers","pointsto","referrers","what","whicherrs"]
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
            "whicherrs   show possible values of the selected error variable"]

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

        if get_setting("goguru_output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name(), 'toggle': False } )
        else:
            window.focus_view(view)

    def write_out(self, result, err):
        """ Write the guru output to a new file.
        """

        def cleanPackageAddr (p):
            return str(p).replace('"', '').replace('(', '').replace(')', '').replace('*', '')

        window = self.view.window()
        view = get_output_view(window)

        jump = False
        # parse guru describe to query go doc
        if self.mode == 'godoc' and  result:
            parts = result.split()

            definitionLine = result.split('\n')[1]
            goType = parts[3]

            package = ''
            identifier = ''
            subparts = []
            
            debug('godoc', 'goType', goType)
            if goType == 'package':
                # /home/username/go/src/myProject/utils/global/global.go:104.24-104.29: reference to package "errors"
                    package = cleanPackageAddr(parts[4])
            elif goType == 'func':
                # /home/username/go/src/myProject/utils/global/global.go:232.9-232.20: reference to method func (*myProject/utils/uid.GUIDGenerator).SetServiceID(ServiceID *string)
                if parts[4] == 'method':
                    parts[4] = str(parts[4].split('(')[0]).split(".")
                    package = parts[4][0]
                    identifier = '.'.join(parts[4][1:])
                # /home/username/go/src/myProject/watchdog/main.go:84.5-84.17: reference to func StartUpClient()
                else:
                    package = "-u "+self.local_package
                    parts[4] = cleanPackageAddr(parts[4]).split(".")
                    identifier = '.'.join(parts[4])

            # /home/username/go/src/myProject/watchdog/main.go:78.10-78.17: reference to method func (*myProject/utils/global.Instance).ExitBool(returnErrorCodePtr *bool)
            # /home/username/go/src/myProject/watchdog/main.go:200.18-200.19: reference to method func (*instanceStats).me() string
            elif goType == 'method':

                parts[5] = cleanPackageAddr(parts[5].split('(')[1])

                if '/' in parts[5]:
                    parts[5] = parts[5].split(".")
                    package = parts[5][0]
                    identifier = '.'.join(parts[5][1:])
                else:
                    parts[5] = parts[5].split(".")
                    package = "-u "+self.local_package
                    identifier = '.'.join(parts[5][1:])

            elif goType == 'interface':
                # /home/username/go/src/myProject/utils/global/global.go:238.16-238.19: reference to interface method func (myProject/utils/crypto.GenericKeyHolder).Init(

                parts[6] = cleanPackageAddr(parts[6]).split('.')
                package = parts[6][0]
                identifier = parts[6][1]

                # /home/username/go/src/myProject/utils/uid/uid.go:99:26: concrete method func (*myProject/utils/uid.GUIDGenerator).SetServiceID(ServiceID *string)
                # /home/username/go/src/myProject/utils/log/log.go:50:2:   implements method (myProject/utils/log.GUIDGenerator).SetServiceID
            else:
                result = goType + " not implemented yet."
                jump = True

            if not jump:
                cmd = "go doc %(package)s %(identifier)s " % {
                "package": package,
                "identifier": identifier} 
                debug("godoc","cmd", cmd)
       
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, env=self.env)
                o, e = proc.communicate()

                result = o.decode('utf-8')

                # comment non go code
                prettierResult = ''
                for line in result.splitlines():
                    if line[0:4] == '    ':
                        prettierResult += '//'+ line + '\n'
                    else:
                        prettierResult += line + '\n'
                result = prettierResult+'\n'+definitionLine
                err = e.decode('utf-8')

        # Run a new command to use the edit object for this view.
        view.run_command('go_guru_write_results', {
            'result': result,
            'err': err})

        if get_setting("goguru_output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

        # jump to definition if is set
        if self.mode == 'definition':
            if get_setting("goguru_jumpto_definition", False):
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
            if char == '\n' and self.view.line_endings() == "Windows":
                byte_offset += 1
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
        if get_setting("goguru_use_golangconfig", False):
            try:
                toolpath, cmd_env = golangconfig.subprocess_info('guru', ['GOPATH', 'PATH'], view=self.view)
                toolpath = os.path.realpath(toolpath)
            except:
                error("golangconfig:", sys.exc_info())
                return
        else:
            toolpath = 'guru'
            cmd_env = shellenv.get_env(for_subprocess=True)[1]
            debug("cmd_env", cmd_env)
            goguru_env = get_setting("goguru_env", {}) 
            debug("goguru_env", goguru_env)
            cmd_env.update(goguru_env)

        debug("final_env", cmd_env)
        self.env = cmd_env

        guru_scope = ",".join(get_setting("goguru_scope", ""))

        # add local package to guru scope
        useCurrentPackage = get_setting("goguru_use_current_package", True)
        debug("goguru_use_current_package", useCurrentPackage)
        if useCurrentPackage:
            current_file_path = os.path.realpath(os.path.dirname(file_path))
            GOPATH = os.path.realpath(cmd_env["GOPATH"])
            GOPATH = os.path.join(GOPATH,"src")
            local_package = os.path.relpath(current_file_path, GOPATH)
            if sublime.platform() == 'windows':
                local_package = local_package.replace('\\', '/')
            debug("GOPATH", GOPATH)
            debug("local_package", local_package)
            self.local_package = local_package
            guru_scope = guru_scope+','+local_package
        guru_scope = guru_scope.strip()
        debug("guru_scope", guru_scope)
        if len(guru_scope) > 0:
            guru_scope = "-scope "+guru_scope

        guru_tags = "-tags \""+" ".join(get_setting("goguru_tags", ""))+"\""

        guru_json = ""
        if get_setting("goguru_json", False):
            guru_json = "-json"

        # Build guru cmd.
        cmd = "%(toolpath)s %(scope)s %(tags)s %(guru_json)s %(mode)s %(file_path)s:%(pos)s" % {
        "toolpath": toolpath,
        "file_path": file_path,
        "pos": pos,
        "guru_json": guru_json,
        "mode": mode,
        "scope": guru_scope,
        "tags": guru_tags}
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
            error(err)
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
        if get_setting("goguru_output", "buffer") == "output_panel":
            self.view.window().run_command('show_panel', {'panel': "output.GoGuru Output" })
        else:
            output_view = get_output_view(self.view.window())
            self.view.window().focus_view(output_view)


class GoGuruOpenResultCommand(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
      if view.name() == "GoGuru Output":
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
            m = re.search("^(.+\.go):([0-9]+).([0-9]+)[-: ]", text)
        
        if m:
            w = view.window()
            new_view = w.open_file(m.group(1) + ':' + m.group(2) + ':' + m.group(3), sublime.ENCODED_POSITION)
            group, index = w.get_view_index(new_view)
            if group != -1:
                w.focus_group(group)


def get_output_view(window):
    view = None
    buff_name = 'GoGuru Output'

    if get_setting("goguru_output", "buffer") == "output_panel":
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
    view.set_syntax_file('Packages/Go/Go.sublime-syntax')

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
        val = sublime.load_settings("GoGuru.sublime-settings").get(key)
    if not val:
        val = sublime.load_settings("Default.sublime-settings").get(key)
    if not val:
        val = default
    return val