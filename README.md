GoGuru [![documentation](https://img.shields.io/badge/info-documentation-blue.svg)](http://alvarolm.github.io/GoGuru/)
=========

GoGuru is a Golang plugin for [SublimeText](http://www.sublimetext.com/) 3 that integrates the Go [guru](https://godoc.org/golang.org/x/tools/cmd/guru) tool.

based on previus work from [waigani](http://github.com/waigani/GoOracle).

the guru tool still is on developent,
check out the plan, the official git repo and the code review if you want to keep up:
* https://docs.google.com/document/d/1UErU12vR7jTedYvKHVNRzGPmXqdMASZ6PfE7B-p6sIg/edit#
* https://go.googlesource.com/tools/+log/master/cmd/guru
* https://go-review.googlesource.com/#/q/guru


Usage
-----

Select, or place your cursor over, a symbol (function, variable, constant etc) and press `ctrl+shift+g`. You will be presented with the following modes of analysis to choose from:

```
	callees	  	show possible targets of selected function call
	callers	  	show possible callers of selected function
	callstack 	show path from callgraph root to selected function
	definition	show declaration of selected identifier
	describe  	describe selected syntax: definition, methods, etc
	freevars  	show free variables of selection
	implements	show 'implements' relation for selected type or method
	peers     	show send/receive corresponding to selected channel op
	pointsto	show variables the selected pointer may point to
	referrers 	show all refs to entity denoted by selected identifier
	what		show basic information about the selected syntax node
	whicherrs	show possible values of the selected error variable
```

Select one and the output will be displayed in a new tab.


Install
-------

Install Sublime Package Control (if you haven't done so already) from http://wbond.net/sublime_packages/package_control. Be sure to restart ST to complete the installation.

Bring up the command palette (default ctrl+shift+p or cmd+shift+p) and start typing Package Control: Install Package then press return or click on that option to activate it. You will be presented with a new Quick Panel with the list of available packages. Type GoGuru and press return or on its entry to install GoGuru. If there is no entry for GoGuru, you most likely already have it installed.

GoOracle has several variables to be set in order to work. These are explained in the comments of the default settings `Preferences > Package Settings > GoOracle > Settings-Default`:

```javascript
{
	// env overwrites the default shell environment vars
	// e.g "env": { "GOPATH": "$HOME/go/bin:$PATH" }
	"env": {},

	// use golangconfig, if false then shellenv will be used to get golang environment variables
	"use_golangconfig": false,

	// use_current_package adds to the guru_scope the current package of the the working file
	"use_current_package" : true,

	// besides showing the result, jump directly to the definition
	"jumpto_definition": true,

	// The output can either be one of: 'buffer', 'output_panel'
	// Buffers can hold results from more than one invocation
	// Output panels sit underneath the editor area and are easily dismissed
	"output": "output_panel",

	// print debug info to the terminal
	"debug": true,

	// guru_scope is an array of scopes of analysis for guru.
	// e.g (for github.com/juju/juju) "guru_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"]
	"guru_scope": [],

	// Set guru's output to json
	"guru_json": false,
}
```
You set your own variables in `Preferences > Package Settings > GoGuru > Settings-User`.

You can also make project specific settings. First save your current workspace as a project `Project > Save as project ...`, then edit your project `Project > Edit Project`. Below is an example which sets up GoOracle to be used on the [github.com/juju/juju](https://github.com/juju/juju) codebase:

```javascript
{
    "folders":
    [
        {
            "follow_symlinks": true,
            "path": "/home/user/go/src/github.com/juju/juju"
        }
    ],
    "settings":
    {
        "GoGuru": {
            "guru_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"],
            "output": "output_panel"
        }
    },
}
```

Default key binding:

```javascript
[
    { "keys": ["ctrl+shift+g"], "command": "go_guru"},
    { "keys": ["ctrl+alt+shift+g"], "command": "go_guru_show_results"},
]
```

You can set your own key binding by copying the above into `Preferences > Keybindings - User` and replacing ctrl+shift+g with your preferred key(s).

You can also set a key binding for a specific mode by adding a "mode" arg, e.g.:

```javascript
    ...
    { "keys": ["ctrl+super+c"], "command": "go_guru", "args": {"mode": "callers"} },
    { "keys": ["ctrl+super+i"], "command": "go_guru", "args": {"mode": "implements"} },
    { "keys": ["ctrl+super+r"], "command": "go_guru", "args": {"mode": "referrers"} },
    ...
```


Dependencies
------------
GoGuru relies on the guru tool. You must install it in order for GoOracle to work. Run the following on your command line:

`go get -u golang.org/x/tools/cmd/guru`


About Go Guru
---------------

- [User Manual](https://docs.google.com/document/d/1SLk36YRjjMgKqe490mSRzOPYEDe0Y_WQNRv-EiFYUyw/view#)
- [Design Document](https://docs.google.com/a/canonical.com/document/d/1WmMHBUjQiuy15JfEnT8YBROQmEv-7K6bV-Y_K53oi5Y/edit#heading=h.m6dk5m56ri4e)
- [GoDoc](https://godoc.org/golang.org/x/tools/cmd/oracle)


Copyright, License & Contributors
=================================

GoGuru is released under the MIT license. See [LICENSE.md](LICENSE.md)

GoGuru is the copyrighted work of *The GoGuru Authors* i.e me ([alvarolm](https://github.com/alvarolm/GoGuru)) and *all* contributors. If you submit a change, be it documentation or code, so long as it's committed to GoGuru's history I consider you a contributor. See [AUTHORS.md](AUTHORS.md) for a list of all the GoGuru authors/contributors.
