# Gitscan: a git repository status viewer

<p align="center"><img src="screenshot.png?raw=true"/></p>

Gitscan is a desktop application for viewing the status of all git repositories on a computer.

A concise table layout shows, for each repo, information such as:
- The presence of untracked/modified files, or modified index
- Numbers and/or names of stashes/tags/remotes/submodules/branches
- The total number of commits by which local branches are ahead/behind the remotes
- Date of last local commit
- A summary of the most recent few commits

The program also offers a convenient and fast way to launch a terminal, IDE or diff for each repository. 

It uses Python and PyQt and is suitable for Linux systems (tested on Ubuntu 22.04).


### Readme Contents

- **[Installation and running](#installation-and-running)**<br>
- **[First time setup](#first-time-setup)**<br>
- **[How to use](#how-to-use)**<br>
- **[Development](#development)**<br>
- **[Changelog](#changelog)**<br>
- **[License](#license)**<br>


## Installation and running

1. Clone this repository into a folder on your Python path
2. Install dependencies with:
```
pip install -r requirements.txt
```
3. Run with:
```
python -m gitscan
```


## First time setup

On first run, you will be prompted to choose a path within which to recursively search for git repositories. After completing this search, the application starts as usual.

You should also use the settings menu to choose the commands which are run to open an IDE or terminal window.

The git diff launcher function uses the git difftool command. Ensure you have chosen a preferred difftool with:
```
git config --global diff.tool <tool e.g. meld>
```


## How to use

- Select a row in the repository table to see a summary of the most recent commits in the lower display pane.
- Additional data and/or explanation of data is shown in tooltip messages in the table cells and table column headers (displayed on mouseover).
- Clicking the icons in the penultimate five columns launches external processes. These are:
    - Open repo folder
    - Run a git diff with difftool: this shows uncommitted modifications, if any, or otherwise shows the last commit.
    - Open a terminal window in the repo folder (defaults to gnome-terminal).
    - Open the project in an IDE (defaults to Microsoft Visual Studio Code).
    - Refresh the repo data (including doing a git fetch, if not disabled in settings).
- You can run a new search for repositories at any time. The resulting list will be saved for future sessions.

### Refresh

- Refresh updates the repository data displayed in the application.
    - Press F5 or use the Action menu to refresh all repositories.
    - Click the penultimate column to refresh a single repository.
- By default, refresh includes executing a ```git fetch``` for each remote.
- No other git operations (e.g. merge/pull/rebase) are executed.
- Fetching can be disabled via the settings menu.

### Authentication

- If a repository has a remote which requires authentication, and fetching is enabled, a system-wide credential cache should be used. For example:
```
git config [--global] credential.helper 'cache --timeout=99999'
git fetch  # then provide your credentials once only, per reboot
```
- If git cannot authenticate: the program will show a warning for that repository and the information will be gathered from local data only.

### Warnings

- The final column may show a warning symbol: more information is available in the mouseover tooltip.
- Fetch failures/timeouts are normally due to lack of authentication, or no internet access.

### Things to note

- **Ahead/behind remotes:** each local branch is compared with its remote tracking branch (if any), on all remotes. For each branch/remote combination, the count of commits ahead/behind is found. The two numbers reported are the sums of these two counts over all branches/remotes in the repository.
- **Git submodules** are not listed as separate repositories, but are listed by name in the submodule column tooltip on their parent repository.
- **Slow fetch:** the program attempts to distinguish between a successful but slow fetch, and a fetch that hangs due to lack of authentication, in a reasonably fast time.
- **Last commit date** is for local branches only, so will not reflect remote commits until they are merged locally.
- **Recent commit summary** in the lower pane is for the currently active local branch only. 


## Development

- **Log level:** can be passed in as a command-line argument. For details, do:
```
python -m gitscan --help
```
- **Tests:** run them with: ```python -m unittest discover tests/```
- **Test coverage:** output a report with: ```./code_coverage.sh``` 

- **To Do:**
    - Add support for Windows and Mac
    - Improve refresh speed
    - Add more user settings, e.g. display preferences


## Changelog

Changes, fixes and additions in each software release version are listed in the [CHANGELOG](CHANGELOG.md)


## License

See the [LICENSE](LICENSE) file for software license rights and limitations (GNU GPL v3).
