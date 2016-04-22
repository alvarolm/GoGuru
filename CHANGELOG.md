GoGuru Changes
----------------

## 0.1.1 [GoOracle]
    * Optionally place your cursor over a symbol instead of selecting it.

## 0.1.2 [GoOracle]
    * Fix bug: default settings were not being read.

## 0.1.3 [GoOracle]
    * setting GOROOT is now optional
    * default settings assume standard Go environment setup
    * Async launching to avoid blocking
	* Keep previous results in output screen (like default find behavior)
	* Clean up output view (mark as scratch, hide line numbers)
	* Make quick panel monospace
	* Add syntax highlighting to output results to show line numbers
		- matches xml, json, and plain output formats
	* Add double-click jump-to support
		- fires on selection change of a line containing a reference
		- matches xml, json, and plain output formats

### 0.1.4 [GoOracle]
	* Support project settings