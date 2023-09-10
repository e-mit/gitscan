"""Define the table column order for table data display."""
from enum import Enum, auto


class Column(Enum):
    """Represent the column order for layout of the main table.

    First enum value is 0, then subsequent increase in the order listed.
    """

    FOLDER = 0
    REPO_NAME = auto()
    UNTRACKED = auto()
    MODIFIED = auto()
    BARE = auto()
    STASH = auto()
    INDEX = auto()
    AHEAD = auto()
    BEHIND = auto()
    TAGS = auto()
    SUBMODULES = auto()
    REMOTES = auto()
    BRANCHES = auto()
    BRANCH_NAME = auto()
    LAST_COMMIT = auto()
    OPEN_FOLDER = auto()
    OPEN_DIFFTOOL = auto()
    OPEN_TERMINAL = auto()
    OPEN_IDE = auto()
    REFRESH = auto()
    WARNING = auto()


left_align = [Column.FOLDER, Column.REPO_NAME,
              Column.BRANCH_NAME, Column.LAST_COMMIT]

column_text = {}  # [Title, tooltip]
column_text[Column.FOLDER] = ["Parent directory", "Parent directory"]
column_text[Column.REPO_NAME] = ["Name", "Repository name"]
column_text[Column.UNTRACKED] = ["U", "Untracked file(s)"]
column_text[Column.MODIFIED] = ["M", "Modified file(s)"]
column_text[Column.BARE] = ["B", "Bare/mirror repository"]
column_text[Column.STASH] = ["S", "At least one stash"]
column_text[Column.INDEX] = ["I", "Index has changes"]
column_text[Column.AHEAD] = ["▲", "Local branches ahead of remotes"]
column_text[Column.BEHIND] = ["▼", "Local branches behind remotes"]
column_text[Column.TAGS] = ["T", "Tag(s)"]
column_text[Column.SUBMODULES] = ["⦾", "Submodule(s)"]
column_text[Column.REMOTES] = ["R", "Remote(s)"]
column_text[Column.BRANCHES] = ["L", "Local branch(es)"]
